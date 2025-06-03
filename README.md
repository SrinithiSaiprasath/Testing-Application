# 🎓 Test Portal

An interactive and secure online testing platform built using Streamlit.

---

## 🚀 Features

* 👨‍🏫 Student login using **email validation**
* 🛠️ Admin dashboard to **upload questions** and **view submissions**
* ⏳ Timed tests with start and end time tracking
* ✅ Supports **MCQ** and **MSQ** question formats
* 📩 Automatic **email notification** of:

  * Test summary to admin
  * Questions and correct answers to the student
* 📅 Easy Excel/CSV question uploads
* 🔐 Role-based access with separate views for Student and Admin
* 💾 Stores test attempts and results

---

## 📁 Project Structure

```
🔹 app.py                  # Main Streamlit app
🔹 requirements.txt        # Python dependencies
🔹 README.md               # Project documentation
```

---

## 🖥️ Running the App

1. **Clone the repository**

   ```bash
   git clone https://github.com/SrinithiSaiprasath/Testing-Application.git
   cd Testing-Application
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Streamlit app**

   ```bash
   streamlit run app.py
   ```

---

## ✍️ Admin Usage

1. Visit the app landing page
2. Click **"I'm an Admin"** button
3. Upload a `.xlsx` file containing the questions
4. Enter a **unique Test ID** and test **duration**
5. Click **"Create Test"**
6. Use the **"View Submissions"** section to view results

### ✅ Question File Format (Excel)

| description         | code\_section | type | option\_1 | option\_2 | option\_3 | option\_4 | answer            | marks | neg\_marks |
| ------------------- | ------------- | ---- | --------- | --------- | --------- | --------- | ----------------- | ----- | ---------- |
| What is Python?     | None          | MCQ  | Language  | Snake     | Java      | C++       | Language          | 1     | 0          |
| Choose correct ones | None          | MSQ  | List      | Tuple     | String    | Int       | \['List','Tuple'] | 2     | 1          |

* `type` should be either `MCQ` or `MSQ`
* `answer` for `MSQ` should be a list of correct options
* `neg_marks` should be 0 if no negative marking

---

## 🧑‍🏫 Student Usage

1. Receive the test link (e.g. `https://your-app-url/?test_id=test123`)
2. Enter your **official email ID** (e.g., `user@domain.net`)
3. Start answering the questions
4. Submit the test once completed

After submission:

* The student will receive an email with the **questions and correct answers**
* The admin receives a **test summary with marks, timings, and counts**

---

## 📧 Email Integration

This app includes a `send_email()` function that can be connected to:

* **Gmail SMTP** using `smtplib`
* Any transactional email service that supports file attachments

You need to configure your email backend separately in `send_email()`.

---

## 📌 Future Enhancements

* 🔒 Admin authentication (password or token)
* 🥒 Real-time timer with automatic submission
* 📊 Analytics dashboard for test performance
* 📟 Export all submissions as CSV
* 🧠 AI-assisted question generation

---

## 🏫 Developed For

Designed for internal use by faculty and students to conduct evaluations easily with automated feedback and tracking.

---

## 📜 License

This project is licensed for academic use. Please contact the maintainers if you would like to reuse it for your organization or contribute improvements.

---
