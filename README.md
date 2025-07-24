# 🛒 E-Commerce Backend API (Django + DRF)

This is the backend for a modern full-featured e-commerce web application, built with **Django**, **Django REST Framework**, and **PostgreSQL**.  
It supports all core e-commerce features and connects to a Next.js + Tailwind frontend.

---

## 🚀 Features

- ✅ JWT authentication (Register, Login, Complete Profile)
- 🛍️ Product catalog with categories & images (Cloudinary)
- 🛒 Cart creation, management & checkout
- 💳 Multiple payment integrations:
  - Stripe
  - PayPal
  - Lipa na M-Pesa (via Safaricom Daraja API)
- ⭐ Product reviews & rating breakdown
- 🧠 Similar product recommendation engine
- 📦 Order management & My Orders view
- 🛡️ Role-based access for admin features
- 🌐 RESTful API (DRF) with pagination & filtering

---

## 📦 Tech Stack

| Layer        | Technology                        |
|--------------|------------------------------------|
| Language     | Python 3.10+                      |
| Backend      | Django, Django REST Framework     |
| Database     | PostgreSQL                        |
| Media        | Cloudinary                        |
| Payments     | Stripe, PayPal, Lipa na M-Pesa    |
| Auth         | JWT / TokenAuth / Session-based   |
| Frontend     | (Connected via API) Next.js       |

---

## ⚙️ Getting Started (Local Setup)

### 1. Clone the Repository

```bash
git clone https://github.com/Brian-Rotich20/django-shop-DRF.git
cd your-backend-repo
