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

    1. Manually Download the dataset from HuggingFace: <https://huggingface.co/datasets/gaia-benchmark/GAIA/tree/main/2023>
    (you will need to clone the repo)
    2. Copy the content of the datasets to `data/validation` and`data/test`

4. **Configure API keys:**

   - Create a `.env` file in the root directory with the following variables:

     ```bash
     OPENAI_API_KEY=<your_openai_api_key>
     TAVILY_API_KEY=<your_tavily_api_key>
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

Here are the results obtained with the agent:

| Dataset     | Level 1 | Level 2 | Level 3 | Average |
|-------------|---------|---------|---------|---------|
| Validation  | 64.2%   |   53.5%  | 38.5%     | 54.55%  |
| Test        |  TBC    |   TBC    |  TBC    |   TBC    |

---
