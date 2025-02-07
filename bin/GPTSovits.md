# GPTSovits

## 命令

* 进入

```
ssh -p 7824 dsj@49.235.180.59
conda activate gptsovits
cd /data/dsj/cfu/sovits/

python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml

```

* tmux

```
tmux new -s cfu
```

* 端口占用

```
lsof -i :9880

```

