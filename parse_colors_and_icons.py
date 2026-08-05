#!/usr/bin/env python3
"""
Extract colors.json and icons.json from civilopedia_export.json and FontIcons atlas files.

Usage:
    python extract_colors_and_icons.py [export_file] [output_dir]
"""

import sys
import os
import json
import base64
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import numpy as np

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    print(f"Writing output to {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_alpha(alpha_val):
    try:
        a = float(alpha_val)
        if a == 1.0 or a == 1:
            return "1"
        if a == 0.0 or a == 0:
            return "0"
        return f"{a:.4g}"
    except (ValueError, TypeError):
        return "1"

def fix_mismatched_stride(pil_img, wrong_width=266, correct_width=256):
    img_array = np.array(pil_img)
    channels = img_array.shape[2] if len(img_array.shape) == 3 else 1
    flat_data = img_array.flatten()
    
    total_pixels = len(flat_data) // channels
    correct_height = total_pixels // correct_width
    usable_length = correct_height * correct_width * channels
    trimmed_data = flat_data[:usable_length]
    reshaped_array = trimmed_data.reshape((correct_height, correct_width, channels))
    return Image.fromarray(reshaped_array.astype('uint8'))

def generate_colors(export_data, output_dir):
    colors_raw = export_data.get('colors', [])
    colors_dict = {}

    if isinstance(colors_raw, list):
        for item in colors_raw:
            if isinstance(item, dict) and 'Type' in item:
                ctype = item['Type']
                r = round(float(item.get('Red', 0)) * 255)
                g = round(float(item.get('Green', 0)) * 255)
                b = round(float(item.get('Blue', 0)) * 255)
                a = format_alpha(item.get('Alpha', 1))
                colors_dict[ctype] = f"rgba({r}, {g}, {b}, {a})"
    elif isinstance(colors_raw, dict):
        for ctype, item in colors_raw.items():
            if isinstance(item, dict):
                r = round(float(item.get('Red', 0)) * 255)
                g = round(float(item.get('Green', 0)) * 255)
                b = round(float(item.get('Blue', 0)) * 255)
                a = format_alpha(item.get('Alpha', 1))
                colors_dict[ctype] = f"rgba({r}, {g}, {b}, {a})"

    if not colors_dict:
        print("WARNING: No colors found in export data. Preserving existing colors.json if present.")
        existing_colors = load_json(os.path.join(output_dir, 'colors.json'))
        if existing_colors:
            colors_dict = existing_colors

    if colors_dict:
        colors_file = os.path.join(output_dir, 'colors.json')
        save_json(colors_file, colors_dict)
        print(f"Generated colors.json with {len(colors_dict)} color entries.")
    return len(colors_dict)

def find_fonticons_dir(base_dir):
    candidates = [
        os.path.join(base_dir, 'FontIcons'),
        os.path.join(base_dir, 'icon'),
        r'D:\civic\fonticons\icon',
        r'D:\civic\fonticons'
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def parse_ggxml(ggxml_path):
    coords = {}
    if not os.path.exists(ggxml_path):
        return coords
    try:
        tree = ET.parse(ggxml_path)
        root = tree.getroot()
        for glyph in root.findall('.//glyph'):
            ch = glyph.get('ch')
            u = int(glyph.get('u', 0))
            v = int(glyph.get('v', 0))
            w = int(glyph.get('width', 0))
            h = int(glyph.get('height', 0))
            if ch is not None:
                coords[str(ch)] = (u, v, w, h)
    except Exception as e:
        print(f"Error parsing GGXML {ggxml_path}: {e}")
    return coords

def find_image_file(fonticons_dir, base_name):
    # Try .dds, .png, etc. with exact case or lowercase
    extensions = ['.dds', '.png', '.DDS', '.PNG']
    for ext in extensions:
        p = os.path.join(fonticons_dir, base_name + ext)
        if os.path.exists(p):
            return p
        p_lower = os.path.join(fonticons_dir, base_name.lower() + ext)
        if os.path.exists(p_lower):
            return p_lower
    return None

def generate_icons(export_data, output_dir):
    base_dir = output_dir
    fonticons_dir = find_fonticons_dir(base_dir)
    if not fonticons_dir:
        print("ERROR: FontIcons directory not found!")
        return 0

    print(f"Using FontIcons assets from: {fonticons_dir}")

    # Load alts.json for alt text overrides
    alts_file = os.path.join(output_dir, 'alts.json')
    alts_dict = load_json(alts_file)

    # texture mappings (base_name, ggxml_name)
    texture_files = {}
    exported_textures = export_data.get('iconFontTextures', [])
    
    if not exported_textures:
        print("WARNING: No iconFontTextures found in export_data!")
    else:
        for tex_info in exported_textures:
            tex_name = tex_info.get('IconFontTexture')
            file_base = tex_info.get('IconFontTextureFile')
            
            if tex_name and file_base:
                base_name = os.path.splitext(file_base)[0]
                ggxml_name = f"{base_name}.ggxml"
                
                texture_files[tex_name] = (base_name, ggxml_name)
                
        print(f"Dynamically loaded {len(texture_files)} texture mappings from JSON.")

    # Load images and parse ggxml for each texture
    textures = {}
    for tex_name, (base_name, ggxml_name) in texture_files.items():
        img_path = find_image_file(fonticons_dir, base_name)
        ggxml_path = os.path.join(fonticons_dir, ggxml_name)

        if img_path and os.path.exists(ggxml_path):
            try:
                img = Image.open(img_path)
                coords = parse_ggxml(ggxml_path)
                textures[tex_name] = {
                    'image': img,
                    'coords': coords
                }
                print(f"Loaded texture {tex_name} ({os.path.basename(img_path)}): {len(coords)} glyphs")
            except Exception as e:
                print(f"Failed to load texture {tex_name}: {e}")

    # Get mappings from export_data (exported from Lua GameInfo.IconFontMapping())
    mappings = export_data.get('iconFontMappings', [])

    if not mappings:
        print("WARNING: No iconFontMappings found in export_data!")
    else:
        print(f"Found {len(mappings)} iconFontMappings in export data (from Lua).")

    icons_dict = {}

    for item in mappings:
        icon_name = item.get('IconName')
        tex_name = item.get('IconFontTexture') or 'ICON_FONT_TEXTURE_DEFAULT'
        mapping_id = str(item.get('IconMapping', ''))

        if not icon_name or not mapping_id:
            continue

        tex_info = textures.get(tex_name)
        if not tex_info:
            continue

        coords = tex_info['coords'].get(mapping_id)
        if not coords:
            continue

        u, v, w, h = coords
        if w <= 0 or h <= 0:
            continue

        try:
            img = tex_info['image']
            cropped = img.crop((u, v, u + w, v + h))

            buffer = io.BytesIO()
            cropped.save(buffer, format='PNG')
            b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

            html_str = f'<img src="data:image/png;base64,{b64_str}" class="civ5-icon" alt="[{icon_name}]" />'
            alt_str = alts_dict.get(icon_name, "")

            icons_dict[icon_name] = {
                'html': html_str,
                'alt': alt_str
            }
        except Exception as e:
            print(f"Error cropping {icon_name}: {e}")

    if icons_dict:
        icons_file = os.path.join(output_dir, 'icons.json')
        save_json(icons_file, icons_dict)
        print(f"Generated icons.json with {len(icons_dict)} icon entries.")

    return len(icons_dict)

def main():
    export_file = sys.argv[1] if len(sys.argv) > 1 else 'civilopedia_export.json'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'

    print(f"Reading export data from: {export_file}")
    export_data = load_json(export_file)

    num_colors = generate_colors(export_data, output_dir)
    num_icons = generate_icons(export_data, output_dir)

    print(f"Processing finished. Colors: {num_colors}, Icons: {num_icons}")

if __name__ == '__main__':
    main()
