const express = require('express');
const cors = require('cors');
const Razorpay = require('razorpay');
const crypto = require('crypto');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const RAZORPAY_KEY_ID = process.env.RAZORPAY_KEY_ID;
const RAZORPAY_KEY_SECRET = process.env.RAZORPAY_KEY_SECRET;

const publicPath = path.join(__dirname);
app.use(express.static(publicPath));

if (!RAZORPAY_KEY_ID || !RAZORPAY_KEY_SECRET) {
  console.error('Missing Razorpay credentials in .env');
  process.exit(1);
}

const razorpay = new Razorpay({
  key_id: RAZORPAY_KEY_ID,
  key_secret: RAZORPAY_KEY_SECRET,
});

app.use(cors({ origin: true }));
app.use(express.json());

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/api/config', (_req, res) => {
  res.json({ razorpay_key_id: RAZORPAY_KEY_ID });
});

app.post('/api/create-order', async (req, res) => {
  const { amount, currency = 'INR', receipt } = req.body || {};

  if (typeof amount !== 'number' || Number.isNaN(amount)) {
    return res.status(400).json({ error: 'Amount must be a number in paise.' });
  }

  if (amount < 100) {
    return res.status(400).json({ error: 'Amount must be at least 100 paise.' });
  }

  try {
    const order = await razorpay.orders.create({
      amount,
      currency,
      receipt: receipt || `rcpt_${Date.now()}`,
    });

    return res.json({
      order_id: order.id,
      amount: order.amount,
      currency: order.currency,
    });
  } catch (error) {
    console.error('Razorpay create order error:', error);
    if (error.statusCode === 401 || error.statusCode === 403) {
      return res.status(401).json({ error: 'Razorpay authentication failed.' });
    }

    return res.status(500).json({ error: 'Unable to create Razorpay order.' });
  }
});

app.post('/api/verify-payment', (req, res) => {
  const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = req.body || {};

  if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature) {
    return res.status(400).json({ error: 'Missing required payment fields.' });
  }

  const generatedSignature = crypto
    .createHmac('sha256', RAZORPAY_KEY_SECRET)
    .update(`${razorpay_order_id}|${razorpay_payment_id}`)
    .digest('hex');

  const signatureBuffer = Buffer.from(generatedSignature, 'utf8');
  const receivedBuffer = Buffer.from(razorpay_signature, 'utf8');

  const isValidSignature =
    signatureBuffer.length === receivedBuffer.length &&
    crypto.timingSafeEqual(signatureBuffer, receivedBuffer);

  if (!isValidSignature) {
    return res.status(400).json({ success: false, error: 'Signature mismatch.' });
  }

  return res.json({ success: true, razorpay_order_id, razorpay_payment_id });
});

app.use((_req, res) => {
  res.status(404).json({ error: 'Not found.' });
});

app.listen(PORT, () => {
  console.log(`Razorpay backend listening on port ${PORT}`);
});
