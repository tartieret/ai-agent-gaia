# GAIA Agent Benchmark

This repository provides an implementation of an AI agent designed to run on the GAIA benchmark.

## Installation

Follow these steps to set up your environment and install the required dependencies:

1. **Create and activate a Python virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install required packages:**
   - Install **Linux system packages** listed in `packages.txt` (using `apt`):

     ```bash
     sudo xargs -a packages.txt apt install -y
     ```

   - Install additional dependencies from `requirements.txt`:

     ```bash
     pip install -r requirements.txt
     ```

   - Install the browser executable:

     ```bash
     playwright install
     ```

3. **Download the GAIA dataset from HuggingFace**:

   ```bash
   wget https://github.com/Anthropic/GAIA/releases/download/v0.1.0/gaia_dataset_v0.1.0.tar.gz
   tar -xvf gaia_dataset_v0.1.0.tar.gz
   ```

## How to Run

You can run the agent using the `run.py` script. Example usage:

```bash
python run.py --dataset <dataset> --level <level>
```

- `<dataset>`: Choose between `validation` or `test`.
- `<level>`: Specify the question level (1, 2, or 3). Optional; runs all levels if not specified.

To run a specific question by its task ID:

```bash
python run.py --dataset <dataset> <task_id>
```

- `<task_id>`: (Optional) ID of the task to run. Runs all if not specified.

To avoid saving the results, add the `--nosave` flag:

```bash
python run.py --dataset <dataset> --level <level> --nosave
```

By default, results are saved in `data/answers`.

## Results

Below is a template table to record the results on each dataset and each level. Please fill in the values manually after running your experiments.

| Dataset     | Level 1 | Level 2 | Level 3 |
|-------------|---------|---------|---------|
| Validation  |         |         |         |
| Test        |         |         |         |

---

- For any issues, please ensure you have activated the virtual environment and installed all dependencies.
- For package requirements, see `packages.txt` and `requirements.txt`.
