# Scripts

## CompreFace smoke test

Safe connection check:

```powershell
.\.venv\Scripts\python.exe .\scripts\compreface_smoke_test.py
```

Create a subject:

```powershell
.\.venv\Scripts\python.exe .\scripts\compreface_smoke_test.py --subject sv001 --create-subject
```

Upload one image or a folder of images:

```powershell
.\.venv\Scripts\python.exe .\scripts\compreface_smoke_test.py --subject sv001 --upload .\dataset\sv001
```

Recognize a test image:

```powershell
.\.venv\Scripts\python.exe .\scripts\compreface_smoke_test.py --recognize .\dataset\sv001\test.jpg --threshold 0.97
```

## Kaggle dataset sample evaluation

Preview the plan without changing CompreFace:

```powershell
.\.venv\Scripts\python.exe .\scripts\compreface_dataset_eval.py --dataset ".\archive\Faces\Faces"
```

Enroll a small sample and test recognition:

```powershell
.\.venv\Scripts\python.exe .\scripts\compreface_dataset_eval.py --dataset ".\archive\Faces\Faces" --max-subjects 3 --enroll-per-subject 5 --test-per-subject 2 --apply
```

Evaluate existing enrolled subjects without uploading duplicates:

```powershell
.\.venv\Scripts\python.exe .\scripts\compreface_dataset_eval.py --dataset ".\archive\Faces\Faces" --max-subjects 3 --enroll-per-subject 5 --test-per-subject 2 --threshold 0.95 --apply --evaluate-only
```
