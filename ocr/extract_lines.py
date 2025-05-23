import os
import xml.etree.ElementTree as ET
from PIL import Image
from pathlib import Path

# Directorios
input_dir = "Train-A"
output_img_dir = "kraken_dataset/lines"
output_txt_dir = "kraken_dataset/texts"

# Crear carpetas de salida
Path(output_img_dir).mkdir(parents=True, exist_ok=True)
Path(output_txt_dir).mkdir(parents=True, exist_ok=True)

# Namespace del formato PAGE XML
namespace = {"ns": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"}

counter = 1  # Contador de líneas

# Procesar todos los archivos XML
for xml_file in Path(input_dir).glob("*.xml"):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error al leer {xml_file.name}: {e}, archivo ignorado.")
        continue

    page = root.find(".//ns:Page", namespace)
    if page is None or "imageFilename" not in page.attrib:
        print(f"Página inválida en {xml_file.name}, archivo ignorado.")
        continue

    img_name = page.attrib["imageFilename"]
    img_path = Path(input_dir) / img_name
    if not img_path.exists():
        print(f"Imagen no encontrada: {img_name}, saltando.")
        continue

    try:
        img = Image.open(img_path)
    except Exception as e:
        print(f"No se pudo abrir la imagen {img_name}: {e}")
        continue

    # Extraer líneas
    for line in root.findall(".//ns:TextLine", namespace):
        coords = line.find(".//ns:Coords", namespace)
        if coords is None:
            continue

        try:
            points = [tuple(map(int, p.split(","))) for p in coords.attrib["points"].split()]
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            xmin, xmax = min(x_coords), max(x_coords)
            ymin, ymax = min(y_coords), max(y_coords)
            cropped = img.crop((xmin, ymin, xmax, ymax))
        except Exception as e:
            print(f"⚠️  Error recortando línea en {xml_file.name}: {e}")
            continue

        img_name_out = f"linea{counter}.png"
        text_name_out = f"linea{counter}.txt"
        cropped.save(Path(output_img_dir) / img_name_out)

        # Extraer texto
        unicode_el = line.find(".//ns:Unicode", namespace)
        text = unicode_el.text.strip() if unicode_el is not None and unicode_el.text else ""
        with open(Path(output_txt_dir) / text_name_out, "w", encoding="utf-8") as f:
            f.write(text)

        counter += 1

print(f"\n✅ Extracción completa: {counter-1} líneas procesadas correctamente.")
