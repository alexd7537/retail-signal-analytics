"""Crea una copia ligera sin publicar ni alterar la entrega completa."""
from pathlib import Path
import argparse,shutil,json
ROOT=Path(__file__).resolve().parents[1]
def prepare(destination):
    destination=destination.resolve()
    if destination==ROOT or ROOT in destination.parents:
        raise ValueError('La copia debe estar fuera de la entrega original.')
    if destination.exists():raise FileExistsError('La carpeta destino existe; usar --output con otra ruta.')
    def ignore(folder,names):
        return {name for name in names if name in {'node_modules','__pycache__','.pbi','.git','.venv','raw','processed','results.json'} or name.endswith(('.sqlite','.abf','.inspect.ndjson','.zip','.pyc'))}
    shutil.copytree(ROOT,destination,ignore=ignore)
    path=destination/'powerbi/OnlineRetail.SemanticModel/model.bim'
    model=json.loads(path.read_text(encoding='utf-8'))
    for param in model['model']['expressions']:
        if param['name']=='DataFolder':param['expression']='"C:/RETAIL_DATA" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    path.write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8')
    prefixes=['C:'+'/'+ 'Users/','C:'+'\\'+'Users'+'\\']
    for file in destination.rglob('*'):
        if file.is_file() and file.suffix.lower() in {'.md','.py','.mjs','.json','.bim','.pq','.dax','.sql'}:
            content=file.read_text(encoding='utf-8')
            if any(prefix in content for prefix in prefixes):
                raise ValueError('Revisar ruta personal en '+str(file.relative_to(destination)))
    print('Copia preparada en',destination)
    print('No se publicó ni se creó un repositorio remoto.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT.parent/'github_retail_signal')
    prepare(parser.parse_args().output)
