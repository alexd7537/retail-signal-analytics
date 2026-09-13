"""Actualiza únicamente DataFolder en model.bim; no reescribe visuales ni medidas."""
from pathlib import Path
import argparse,json,csv
ROOT=Path(__file__).resolve().parents[1]
def configure(folder):
    folder=folder.resolve(strict=True)
    for filename in ['FactTransactions.csv','DimProduct.csv','DimCustomer.csv','DimCountry.csv','DimDate.csv','reconciliation.csv']:
        if not (folder/filename).is_file():raise FileNotFoundError(folder/filename)
    with (folder/'DimProduct.csv').open(encoding='utf-8-sig',newline='') as stream:
        codes=[row['StockCode'] for row in csv.DictReader(stream)]
    if len(codes)!=len({c.strip().casefold() for c in codes}):
        raise ValueError('DimProduct tiene códigos repetidos sin distinguir mayúsculas. Reconstruir con analyze.py.')
    path=ROOT/'powerbi/OnlineRetail.SemanticModel/model.bim'
    if not path.is_file():raise FileNotFoundError('Se requiere el model.bim TMSL entregado. No se modifica un modelo convertido a TMDL.')
    data=json.loads(path.read_text(encoding='utf-8'))
    param=next(x for x in data['model']['expressions'] if x['name']=='DataFolder')
    param['expression']='"'+folder.as_posix().replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('DataFolder configurado. Diseño y medidas conservados. Abrir Power BI y actualizar.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True)
    configure(parser.parse_args().folder)
