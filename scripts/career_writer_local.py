"""Prepare pinned free local inference; no paid API and no backend/.env access."""
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

workspace=Path(__file__).resolve().parents[1]
root=workspace / '.local/career-writer'
root.mkdir(parents=True,exist_ok=True)
assets=[('llama.zip','https://github.com/ggml-org/llama.cpp/releases/download/b11609/llama-b11609-bin-win-cpu-x64.zip','8708a7b81842333927f6377ac3f17ff8bba4dbe1ee0cf28dfd5e7a32e3a46b38'),('qwen2.5-1.5b-instruct-q4_k_m.gguf','https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/91cad51170dc346986eccefdc2dd33a9da36ead9/qwen2.5-1.5b-instruct-q4_k_m.gguf','6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e')]
for name,url,expected in assets:
    destination=root/name
    if not destination.exists():
        print('Descargando '+name,flush=True)
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'TalentSync-local-setup'}),timeout=60) as response, destination.open('wb') as output:
            while chunk:=response.read(1024*1024): output.write(chunk)
    h=hashlib.sha256()
    with destination.open('rb') as stream:
        while chunk:=stream.read(1024*1024): h.update(chunk)
    if h.hexdigest()!=expected: raise SystemExit('El hash no coincide: '+name)
    print('Verificado '+name,flush=True)
with zipfile.ZipFile(root/'llama.zip') as archive:
    target=(root/'runtime').resolve()
    for item in archive.infolist():
        if not (target/item.filename).resolve().is_relative_to(target): raise SystemExit('Ruta de archivo inválida')
    archive.extractall(target)
print(json.dumps({'ready':True,'executables':[p.name for p in (root/'runtime').rglob('*.exe')]}),flush=True)

config=workspace / '.local/backend.env'
if not config.is_file(): raise SystemExit('Prepara primero el entorno local aislado')
values={'CAREER_WRITER_MODEL':(root/'qwen2.5-1.5b-instruct-q4_k_m.gguf').as_posix(),'CAREER_WRITER_EXECUTABLE':(root/'runtime/llama-completion.exe').as_posix()}
lines=[line for line in config.read_text(encoding='utf-8').splitlines() if not any(line.startswith(key+'=') for key in values)]
config.write_text('\n'.join([*lines,*(f'{key}={value}' for key,value in values.items())])+'\n',encoding='utf-8')
(root/'provenance.json').write_text(json.dumps({'model_revision':'91cad51170dc346986eccefdc2dd33a9da36ead9','runtime_release':'b11609','model_sha256':assets[1][2],'runtime_sha256':assets[0][2],'scope':'local inference; no paid API; no CV upload'},indent=2),encoding='utf-8')
print('IA local preparada. Reinicia la API. No se ha configurado ningún proveedor de pago.')
