import argparse,json
from pathlib import Path
from .inference import predict_crop_and_yield
def main():
    parser=argparse.ArgumentParser(description='AgroIntel local prediction')
    parser.add_argument('request',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        result=predict_crop_and_yield(json.loads(args.request.read_text()))
    except (ValueError,OSError) as exc:
        parser.exit(2,f'Prediction failed: {exc}\n')
    text=json.dumps(result,indent=2,allow_nan=False)
    if args.output:
        args.output.write_text(text,encoding='utf-8')
    print(text)
if __name__=='__main__':
    main()
