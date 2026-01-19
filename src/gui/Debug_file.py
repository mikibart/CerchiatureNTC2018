#!/usr/bin/env python3
"""
Fix per main_window.py dalla directory corrente
"""

import os
import chardet

# Usa il nome file direttamente, non il percorso completo
filename = "main_window.py"

print(f"Directory corrente: {os.getcwd()}")
print(f"Cercando il file: {filename}")

if not os.path.exists(filename):
    print(f"\n❌ File {filename} non trovato!")
    print("\nFile presenti nella directory:")
    for f in os.listdir('.'):
        if f.endswith('.py'):
            print(f"  - {f}")
    exit(1)

print(f"✓ File trovato!")

# Rileva encoding
with open(filename, 'rb') as f:
    raw_data = f.read()
    result = chardet.detect(raw_data)
    print(f"\nEncoding rilevato: {result['encoding']} (confidenza: {result['confidence']:.2f})")

# Mostra info sul file
print(f"Dimensione file: {len(raw_data)} bytes")

# Prova a leggere il file
content = None
for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
    try:
        with open(filename, 'r', encoding=encoding) as f:
            content = f.read()
        print(f"✓ Letto con successo usando: {encoding}")
        break
    except Exception as e:
        print(f"✗ Errore con {encoding}: {type(e).__name__}")

if content is None:
    print("\nLeggo ignorando errori...")
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

# Analizza le linee problematiche
lines = content.split('\n')
print(f"\nTotale linee: {len(lines)}")

if len(lines) >= 752:
    print("\n--- Analisi linee 750-754 ---")
    for i in range(749, min(754, len(lines))):
        line = lines[i]
        indent = len(line) - len(line.lstrip())
        print(f"Linea {i+1} (indent={indent}): {repr(line[:60])}...")

# Correggi il file
print("\n" + "="*50)
response = input("Vuoi correggere il file? (s/n): ")

if response.lower() == 's':
    # Backup
    import shutil
    backup = filename + '.backup'
    shutil.copy2(filename, backup)
    print(f"Backup salvato: {backup}")
    
    # Correggi caratteri problematici
    content_fixed = content
    replacements = {
        '\u2019': "'", '\u2018': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-',
        '\xa0': ' ', '\u200b': ''
    }
    
    for old, new in replacements.items():
        if old in content_fixed:
            content_fixed = content_fixed.replace(old, new)
            print(f"Sostituito: {repr(old)} -> {repr(new)}")
    
    # Correggi indentazione della linea 752
    lines = content_fixed.split('\n')
    
    # Controlla se la linea 752 è un "else:" mal indentato
    if len(lines) > 751 and lines[751].strip() == 'else:':
        print(f"\nCorrezione linea 752 (else:)...")
        # Trova l'if corrispondente
        for j in range(750, -1, -1):
            if 'if ' in lines[j] and ':' in lines[j]:
                indent = len(lines[j]) - len(lines[j].lstrip())
                lines[751] = ' ' * indent + 'else:'
                print(f"Indentazione corretta: {indent} spazi")
                break
    
    content_fixed = '\n'.join(lines)
    
    # Salva
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content_fixed)
    
    print(f"\n✓ File {filename} corretto!")
    print("\nOra torna alla directory principale:")
    print("  cd ../..")
    print("  python main.py")