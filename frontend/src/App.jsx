import { useState } from 'react';
import {
  ArrowRight,
  CircleAlert,
  LoaderCircle,
  Shield,
  ShieldCheck,
} from 'lucide-react';
import { apiPost } from './services/api';

const initialForm = {
  transaction_type: 'TRANSFER',
  hour: '14',
  amount: '1250',
  sender_balance_before: '5000',
  sender_balance_after: '3750',
  receiver_balance_before: '10000',
  receiver_balance_after: '11250',
};

const fields = [
  { name: 'hour', label: 'Transaction hour', min: 0, max: 23, step: 1, help: '24-hour local time' },
  { name: 'amount', label: 'Transaction amount', min: 0, step: '0.01', help: 'Amount in the transaction currency' },
  { name: 'sender_balance_before', label: 'Sender balance before', min: 0, step: '0.01' },
  { name: 'sender_balance_after', label: 'Sender balance after', min: 0, step: '0.01' },
  { name: 'receiver_balance_before', label: 'Receiver balance before', min: 0, step: '0.01' },
  { name: 'receiver_balance_after', label: 'Receiver balance after', min: 0, step: '0.01' },
];

const formatPercent = (value) =>
  new Intl.NumberFormat('en-US', {
    style: 'percent',
    maximumFractionDigits: 1,
  }).format(value);

function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateForm = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const payload = Object.fromEntries(
        Object.entries(form).map(([name, value]) => [
          name,
          name === 'transaction_type' ? value : Number(value),
        ]),
      );
      setResult(await apiPost('/api/predict', payload));
    } catch (submitError) {
      setError(submitError.message || 'The transaction could not be scored. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const highRisk = result?.prediction === 'high_risk';

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Tranzacta home">
          <span className="brand-mark"><Shield aria-hidden="true" /></span>
          <span className="brand-copy">
            <strong>Tranzacta</strong>
            <small>See the risk. Stop the fraud.</small>
          </span>
        </a>
      </header>

      <main className="main-content">
        <form className="form-card" onSubmit={submit}>
          <div className="form-heading">
            <h1>Transaction details</h1>
            <p>Enter transaction information to assess its risk.</p>
          </div>

          <label className="field" htmlFor="transaction_type">
            <span>Transaction type</span>
            <select
              id="transaction_type"
              name="transaction_type"
              value={form.transaction_type}
              onChange={updateForm}
            >
              <option value="TRANSFER">Transfer</option>
              <option value="CASH_OUT">Cash out</option>
            </select>
          </label>

          <div className="field-grid">
            {fields.map((field) => (
              <label className="field" key={field.name} htmlFor={field.name}>
                <span>{field.label}</span>
                <input
                  id={field.name}
                  name={field.name}
                  type="number"
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  required
                  value={form[field.name]}
                  onChange={updateForm}
                />
                {field.help && <small>{field.help}</small>}
              </label>
            ))}
          </div>

          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? (
              <>
                <LoaderCircle size={17} className="spin" />
                Assessing transaction
              </>
            ) : (
              <>
                Assess transaction
                <ArrowRight size={17} />
              </>
            )}
          </button>

          {error && <p className="error-message" role="alert">{error}</p>}

          {result && (
            <output className={`result-message ${highRisk ? 'result-high' : 'result-low'}`} aria-live="polite">
              <span className="result-icon">
                {highRisk ? <CircleAlert size={19} /> : <ShieldCheck size={19} />}
              </span>
              <span className="result-copy">
                <strong>{highRisk ? 'Elevated risk detected' : 'Lower risk signal'}</strong>
                <span>
                  {formatPercent(result.fraud_probability)} fraud probability
                  {' · '}threshold {formatPercent(result.threshold)}
                </span>
                <span>{result.recommendation}</span>
              </span>
            </output>
          )}
        </form>
      </main>
    </div>
  );
}

export default App;
