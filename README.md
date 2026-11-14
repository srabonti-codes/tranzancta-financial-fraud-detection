# Tranzacta

Tranzacta is a transaction-risk scoring showcase that pairs a React interface with a FastAPI service and a Keras fraud-classification model. It demonstrates request validation, transaction feature engineering, model inference, and an experimental notebook-based training workflow.

The model was developed with synthetic PaySim mobile-money data. Its scores are educational decision support only, not a guarantee of fraud or a substitute for an institution's fraud controls, investigation, or regulatory obligations.

## Project overview

The frontend collects a transaction type, hour, amount, and sender/receiver balances. The API validates the request, derives the model features, scales them with the saved preprocessing object, and returns a fraud-risk score and threshold-based recommendation.

This is a source-only release. The dataset and generated model, preprocessing, and evaluation artifacts are not included. The API starts without them in a degraded state; prediction requests return `503` until local artifacts are generated.

## Features

- React transaction review form and risk-result presentation.
- FastAPI endpoints for health, model information, metrics, and prediction.
- Pydantic validation of supported transaction types, numeric ranges, and unexpected fields.
- Feature engineering for log amount, balance inconsistencies, transaction hour, night-time activity, high-value amounts, and transaction type.
- A Keras model and saved scaler can be loaded from local generated artifacts.
- Four Jupyter notebooks for preprocessing, model training, model selection/evaluation, and inference.
- Focused API tests that do not require a published model artifact.

## Transaction review experience

The user enters one of the supported transaction types (`TRANSFER` or `CASH_OUT`) and the transaction's time, amount, and before/after balances. The interface submits these values to `POST /api/predict` and displays the model's risk classification and probability. The response is a model estimate and should not be used as an automatic basis for blocking a payment or accusing a person.

## Roles and permissions

The project has no account system, role-based permissions, or authentication. There are no separate customer, analyst, or administrator roles. The demo form and API are available without sign-in; do not use them to process sensitive real-world financial data or expose the API publicly without adding appropriate access controls, abuse protection, and operational monitoring.

## Technology

| Area | Technologies |
|---|---|
| Frontend | React 18, Vite 6, Tailwind CSS 4, Lucide React |
| API | Python, FastAPI, Pydantic, Uvicorn |
| Inference and preprocessing | TensorFlow/Keras, NumPy, pandas, scikit-learn |
| Research workflow | Jupyter, PyTorch, PyTorch TabNet, Matplotlib |
| Tests | pytest, FastAPI TestClient |

Dependency versions are recorded in `frontend/package.json`, `frontend/package-lock.json`, and `backend/requirements.txt`. Additional notebook dependencies are in `backend/notebooks/requirements.txt`.

## Architecture

```text
Browser
  └── React + Vite
        └── POST /api/predict
              └── FastAPI / Pydantic validation
                    └── Transaction feature engineering
                          └── Local preprocessing scaler
                                └── Local Keras model
                                      └── Risk score and recommendation
```

The serving API currently loads a Keras model and its preprocessing bundle from `backend/models/` and `backend/artifacts/`. The research notebooks also train non-Keras models; the API does not currently serve those model families.

## Repository structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py
│   │   ├── services/fraud_service.py
│   │   ├── config.py
│   │   ├── main.py
│   │   └── schemas.py
│   ├── data/README.md
│   ├── notebooks/
│   │   ├── preprocessing_pipeline.ipynb
│   │   ├── model_training.ipynb
│   │   ├── result_analysis.ipynb
│   │   ├── model_inference.ipynb
│   │   └── requirements.txt
│   ├── requirements.txt
│   └── tests/test_api.py
├── frontend/
│   ├── public/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── LICENSE
└── README.md
```

## Prerequisites

- Python 3.11
- Node.js 18 or newer and npm

## Local setup

### Backend

From `backend/`, create an environment and install the serving dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the API from `backend/`:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API documentation is available at `http://localhost:8000/api/docs`. Without local model artifacts, `/api/health` reports a degraded state and `/api/predict` returns `503`.

### Frontend

In a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Open the Vite URL printed in the terminal. The development server proxies `/api` requests to `http://localhost:8000`.

## Environment configuration

The example files contain local development settings only:

| File | Variable | Purpose |
|---|---|---|
| `backend/.env.example` | `APP_ENV`, `APP_NAME`, `APP_VERSION` | API metadata |
| `backend/.env.example` | `ALLOWED_ORIGINS` | Comma-separated browser origins permitted by CORS |
| `backend/.env.example` | `MODEL_PATH`, `MODEL_METADATA_PATH`, `PREPROCESSING_PATH` | Paths to locally generated inference artifacts |
| `frontend/.env.example` | `VITE_API_URL` | Optional API origin; Vite uses the local proxy when unset |

Never put credentials or private values in `VITE_*` variables: Vite embeds them in browser code. Do not commit `.env` or `.env.local` files.

## Development commands

| Location | Command | Purpose |
|---|---|---|
| `frontend/` | `npm run dev` | Start the Vite development server |
| `frontend/` | `npm run build` | Build frontend assets into the ignored `dist/` directory |
| `frontend/` | `npm run preview` | Preview a previously created build |
| `backend/` | `python -m pytest tests` | Run backend tests |
| `backend/` | `python -m uvicorn app.main:app --reload` | Run the local API |

## Dataset and model workflow

The raw dataset is not redistributed in this repository. The notebooks are based on the Kaggle [Synthetic Financial Datasets For Fraud Detection (PaySim)](https://www.kaggle.com/datasets/ealaxi/paysim1), listed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Review the source terms, provide attribution, and indicate any changes when using or sharing the dataset. The commonly used source paper is E. A. Lopez-Rojas, A. Elmir, and S. Axelsson, “PaySim: A financial mobile money simulator for fraud detection,” EMSS, 2016.

The Kaggle listing does not explicitly settle whether model weights trained from the dataset are adapted material under ShareAlike. To avoid making that licensing determination for users, this release excludes trained weights and dataset-derived preprocessing and evaluation artifacts.

To reproduce the local workflow:

1. Obtain the dataset from a source whose terms permit your intended use and place the full CSV at `backend/data/transactions.csv`.
2. From `backend/`, install the optional research dependencies:

   ```powershell
   python -m pip install -r notebooks/requirements.txt
   python -m jupyter lab notebooks/
   ```

3. Run the notebooks in this order: `preprocessing_pipeline.ipynb`, `model_training.ipynb`, then `result_analysis.ipynb`. `model_inference.ipynb` demonstrates scoring after model artifacts have been generated.
4. The notebooks write local data, candidate models, evaluation results, and selected model artifacts under `backend/data/`, `backend/artifacts/`, `backend/models/`, and `backend/results/`; these outputs are ignored by Git.

`model_training.ipynb` evaluates several model families, while the API currently requires a Keras model. If the selected model is not Keras, it cannot be loaded by this API without an implementation change. Generated Keras models and preprocessing objects are not included in this release. Only load locally generated or otherwise trusted pickle artifacts.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Service metadata |
| `GET` | `/health` | Service and model readiness |
| `GET`, `HEAD` | `/api/health` | API and model readiness |
| `GET` | `/api/model-info` | Model name, features, and supported transaction types |
| `GET` | `/api/metrics` | Available model evaluation metadata |
| `POST` | `/api/predict` | Score a transaction |

Example request:

```json
{
  "transaction_type": "TRANSFER",
  "hour": 14,
  "amount": 1250.0,
  "sender_balance_before": 5000.0,
  "sender_balance_after": 3750.0,
  "receiver_balance_before": 10000.0,
  "receiver_balance_after": 11250.0
}
```

## Security and implementation notes

- The API has no authentication or rate limiting. Treat it as a local demonstration; add appropriate safeguards before hosting it for public or financial use.
- Vite development and preview servers bind to loopback by default; do not override the host to expose them on an untrusted network.
- CORS allows only configured origins, disables credentials, and restricts methods and headers.
- Inputs are validated and extra request fields are rejected, but valid values are not proof that a transaction is legitimate.
- The preprocessing bundle uses Python pickle. Unpickling an untrusted file can execute code; use only artifacts you generated or otherwise trust.
- The dataset is synthetic and may not represent real-world transactions, customer behavior, or current fraud patterns. Model estimates are not financial or compliance advice.
- The MIT license in this repository applies to original Tranzacta code. The PaySim dataset is not included; its separate license and attribution requirements continue to apply to any copy obtained by users.
- No production deployment is configured in this source-only release.
