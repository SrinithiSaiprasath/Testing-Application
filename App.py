import streamlit as st
import pandas as pd
import uuid
import smtplib
import os
import tempfile
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- Configuration and In-Memory Database ---
# For a production app, use environment variables or a proper database
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") # Use app-specific passwords for Gmail

# In-memory stores (will reset on app rerun/refresh)
if 'admin_credentials' not in st.session_state:
    st.session_state.admin_credentials = {ADMIN_EMAIL: ADMIN_PASSWORD}
if 'uploaded_tests' not in st.session_state:
    st.session_state.uploaded_tests = {}  # Stores test data created by admin
if 'student_submissions' not in st.session_state:
    st.session_state.student_submissions = {} # Stores student submission summaries

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="CIT Chennai Test Portal", layout="wide")

# --- Helper Functions ---

def send_email(to_address, subject, body, attachment_path=None):
    """Sends an email with an optional attachment."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_address
        msg['Subject'] = subject

        # Attach body as plain text
        msg.attach(MIMEBase('text', 'plain', charset='utf-8'))
        msg.get_payload()[0].set_payload(body)

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                msg.attach(part)
        else:
            st.warning(f"Attachment not found at: {attachment_path}")

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        st.success(f"Email sent successfully to {to_address}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}. Please check your email credentials and app password.")
        st.info("For Gmail, you might need to generate an 'App password' for your account if 2FA is enabled.")


def authenticate_admin(email, password):
    """Authenticates admin credentials."""
    return st.session_state.admin_credentials.get(email) == password

def go_to_page(page_name):
    """Changes the current page in session state."""
    st.session_state.page = page_name
    # st.experimental_rerun() # Rerun to immediately update the page


# --- Page Layout Functions ---

def landing_page():
    """Displays the initial landing page for admin/student choice."""
    st.title("Welcome to the CIT Chennai Test Portal")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.header("For Students")
        st.markdown("If you have a test token, click below to start your test.")
        if st.button("I'm a Student", use_container_width=True):
            go_to_page("student_token_entry")
    with col2:
        st.header("For Admins")
        st.markdown("If you are an administrator, log in to create and manage tests.")
        if st.button("I'm an Admin", use_container_width=True):
            go_to_page("admin_login")
    st.markdown("---")


def admin_login_page():
    """Handles admin login."""
    st.title("Admin Login")
    st.markdown("---")
    email = st.text_input("Admin Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_admin(email, password):
            st.session_state.admin_authenticated = True
            go_to_page("admin_dashboard")
        else:
            st.error("Invalid credentials. Please try again.")
    if st.button("Back to Home"):
        go_to_page("landing")
    st.markdown("---")


def admin_dashboard_page():
    """Allows admins to upload tests and generate links."""
    if not st.session_state.get("admin_authenticated"):
        st.warning("Please log in as an administrator to access this page.")
        go_to_page("admin_login")
        return

    st.title("Admin Dashboard")
    st.markdown("---")

    st.subheader("Create New Test")
    test_name = st.text_input("Enter Test Name", key="new_test_name")
    duration_minutes = st.number_input("Test Duration (in minutes)", min_value=1, value=60, key="new_test_duration")
    uploaded_file = st.file_uploader("Upload Questions CSV", type=["csv"], key="new_test_upload")

    if uploaded_file and test_name and duration_minutes:
        try:
            test_df = pd.read_csv(uploaded_file)
            # Validate CSV columns
            required_cols = ['description', 'type', 'option_1', 'option_2', 'option_3', 'option_4', 'answer', 'marks', 'neg_marks']
            if not all(col in test_df.columns for col in required_cols):
                st.error(f"Missing required columns in CSV. Ensure these columns are present: {', '.join(required_cols)}")
                st.dataframe(test_df.columns.tolist())
                return

            st.write("Preview of Test Questions:")
            st.dataframe(test_df)

            if st.button("Generate Test Link"):
                token = str(uuid.uuid4())[:8]  # 8-char token
                st.session_state.uploaded_tests[token] = {
                    "name": test_name,
                    "data": test_df,
                    "duration": duration_minutes,
                    "created_at": datetime.now()
                }
                st.success("Test Created Successfully!")
                test_url = f"http://localhost:8501/?page=student_token_entry&token={token}" # Adjust host if deploying
                st.markdown(f"**Share this test token with students:** `{token}`")
                st.markdown(f"**Or share this direct link:** [Test Link]({test_url})")
        except Exception as e:
            st.error(f"Error processing CSV file: {e}")
            st.info("Please ensure your CSV is correctly formatted. It should include columns like 'description', 'type', 'option_1'...'option_4', 'answer', 'marks', 'neg_marks', and optionally 'code_section'.")

    st.markdown("---")
    st.subheader("Manage Existing Tests")
    if st.session_state.uploaded_tests:
        test_tokens = list(st.session_state.uploaded_tests.keys())
        selected_token = st.selectbox("Select a test to manage:", [""] + test_tokens)

        if selected_token:
            test_info = st.session_state.uploaded_tests[selected_token]
            st.write(f"**Test Name:** {test_info['name']}")
            st.write(f"**Duration:** {test_info['duration']} minutes")
            st.write(f"**Created On:** {test_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**Test Token:** `{selected_token}`")
            test_url = f"http://localhost:8501/?page=student_token_entry&token={selected_token}"
            st.markdown(f"**Direct Link:** [Test Link]({test_url})")

            # Option to view submissions
            st.subheader(f"Submissions for {test_info['name']}")
            if st.session_state.student_submissions:
                filtered_submissions = {
                    email: data for email, data in st.session_state.student_submissions.items()
                    if data.get('test_token') == selected_token # Filter by test token
                }
                if filtered_submissions:
                    submissions_df = pd.DataFrame(list(filtered_submissions.values()))
                    st.dataframe(submissions_df)

                    csv_buffer = submissions_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Submissions CSV",
                        data=csv_buffer,
                        file_name=f"{test_info['name']}_submissions.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("No submissions yet for this test.")
            else:
                st.info("No submissions recorded yet.")
    else:
        st.info("No tests have been created yet.")

    st.markdown("---")
    if st.button("Logout"):
        st.session_state.admin_authenticated = False
        go_to_page("landing")


def student_token_entry_page():
    """Allows students to enter test token and email."""
    st.title("Enter Test Token and Email")
    st.markdown("---")
    token = st.text_input("Enter Test Token", key="student_token_input")
    email = st.text_input("Enter your CIT Chennai Email", key="student_email_input")

    if st.button("Start Test"):
        if not email.endswith("@citchennai.net"):
            st.error("Only @citchennai.net email IDs are allowed to take this test.")
            return
        elif token not in st.session_state.uploaded_tests:
            st.error("Invalid or expired test token. Please check your link or token.")
            return
        else:
            # Check if student has already submitted this test
            student_submitted_this_test = False
            for submission_email, submission_data in st.session_state.student_submissions.items():
                if submission_email == email and submission_data.get('test_token') == token:
                    student_submitted_this_test = True
                    break

            if student_submitted_this_test:
                st.warning("You have already submitted this test. You cannot retake it.")
                return

            st.session_state.test_id = token
            st.session_state.student_email = email
            st.session_state.test_start_time = datetime.now()
            go_to_page("student_test")
    if st.button("Back to Home"):
        go_to_page("landing")
    st.markdown("---")


def student_test_page():
    """Presents the test questions to the student and handles submission."""
    token = st.session_state.get("test_id")
    student_email = st.session_state.get("student_email")

    if not token or token not in st.session_state.uploaded_tests or not student_email:
        st.error("Invalid test session. Please go back to the student entry page.")
        if st.button("Go to Student Entry"):
            go_to_page("student_token_entry")
        return

    test_info = st.session_state.uploaded_tests[token]
    questions_df = test_info['data']
    test_duration = test_info['duration'] # in minutes
    start_time = st.session_state.get("test_start_time")

    if not start_time:
        st.error("Test start time not recorded. Please restart the test.")
        if st.button("Restart Test"):
            go_to_page("student_token_entry")
        return

    time_elapsed = datetime.now() - start_time
    remaining_time_seconds = (test_duration * 60) - time_elapsed.total_seconds()

    if remaining_time_seconds <= 0:
        st.warning("Time's up! Your test will be submitted automatically.")
        submit_student_test(token, student_email, questions_df, test_info['name'], timed_out=True)
        return

    minutes_left = int(remaining_time_seconds // 60)
    seconds_left = int(remaining_time_seconds % 60)

    st.title(f"Test: {test_info['name']}")
    st.info(f"Time Remaining: {minutes_left:02d}:{seconds_left:02d}")

    # Display questions
    student_answers = {}
    for idx, row in questions_df.iterrows():
        st.markdown(f"---")
        st.markdown(f"### Q{idx+1}: {row['description']}")
        if pd.notna(row.get('code_section')) and row['code_section'].strip():
            st.code(row['code_section'], language='python') # Assuming Python for code sections

        options = [row[f"option_{i}"] for i in range(1, 5) if pd.notna(row[f"option_{i}"])]

        if row['type'].upper() == "MCQ":
            student_answers[idx] = st.radio("Select One:", options, key=f"q{idx}_mcq")
        elif row['type'].upper() == "MSQ":
            student_answers[idx] = st.multiselect("Select Multiple:", options, key=f"q{idx}_msq")
        else:
            st.warning(f"Unknown question type: {row['type']} for Q{idx+1}. Skipping.")

    if st.button("Submit Test", type="primary"):
        submit_student_test(token, student_email, questions_df, test_info['name'], student_answers)

    # Auto-refresh for timer
    # time.sleep(1)
    # st.experimental_rerun()


def submit_student_test(token, student_email, questions_df, test_name, student_answers=None, timed_out=False):
    """Processes student submission, calculates score, and sends emails."""
    if student_answers is None:
        student_answers = {} # Initialize if not provided (e.g., on timeout)

    end_time = datetime.now()
    start_time = st.session_state.get("test_start_time", end_time) # Fallback if start_time is missing

    summary = {
        "Test Name": test_name,
        "Test Token": token,
        "Student Email": student_email,
        "Start Time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "End Time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "Duration Taken (minutes)": round((end_time - start_time).total_seconds() / 60, 2),
        "Total Questions": len(questions_df),
        "Correct Answers": 0,
        "Incorrect Answers": 0,
        "Skipped Questions": 0,
        "Total Marks Obtained": 0
    }

    detailed_results = []

    for idx, row in questions_df.iterrows():
        question_desc = row['description']
        correct_ans = str(row['answer'])
        marks = row['marks']
        neg_marks = row['neg_marks']
        question_type = row['type'].upper()

        current_student_ans = student_answers.get(idx)
        is_correct = False
        marks_awarded = 0

        if current_student_ans is None or current_student_ans == '':
            summary['Skipped Questions'] += 1
            status = "Skipped"
        else:
            if question_type == "MCQ":
                if str(current_student_ans) == correct_ans:
                    is_correct = True
            elif question_type == "MSQ":
                # For MSQ, correct_ans in CSV should be a string of comma-separated options (e.g., "option_1,option_3")
                # Student answer will be a list
                correct_options_set = set(correct_ans.split(','))
                student_options_set = set(current_student_ans)
                if correct_options_set == student_options_set:
                    is_correct = True
            else:
                # Fallback for unknown types or direct input (if implemented)
                if str(current_student_ans) == correct_ans:
                    is_correct = True

            if is_correct:
                summary['Correct Answers'] += 1
                marks_awarded = marks
                status = "Correct"
            else:
                summary['Incorrect Answers'] += 1
                marks_awarded = -neg_marks
                status = "Incorrect"

        summary['Total Marks Obtained'] += marks_awarded

        detailed_results.append({
            "Question": question_desc,
            "Your Answer": str(current_student_ans),
            "Correct Answer": correct_ans,
            "Status": status,
            "Marks Awarded": marks_awarded
        })

    st.session_state.student_submissions[student_email] = summary
    st.session_state.student_submissions[student_email]['detailed_results'] = detailed_results

    st.success("Test submitted successfully!")
    if timed_out:
        st.warning("Your test was submitted automatically because the time ran out.")
    else:
        st.success("You'll receive a detailed summary and the questions with correct answers via email shortly.")


    # Prepare and send emails
    df_summary = pd.DataFrame([summary])
    df_detailed_results = pd.DataFrame(detailed_results)

    # 1. Email to Facilitator
    facilitator_email_body = (
        f"A student has submitted a test.\n\n"
        f"Test Name: {test_name}\n"
        f"Student Email: {student_email}\n"
        f"Total Marks: {summary['Total Marks Obtained']}\n"
        f"Correct: {summary['Correct Answers']}, Incorrect: {summary['Incorrect Answers']}, Skipped: {summary['Skipped Questions']}\n"
        f"Duration Taken: {summary['Duration Taken (minutes)']:.2f} minutes\n\n"
        f"Please find the summary and detailed results attached."
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        summary_path = os.path.join(tmpdir, f"Summary_{student_email.split('@')[0]}_{token}.xlsx")
        detailed_path = os.path.join(tmpdir, f"DetailedResults_{student_email.split('@')[0]}_{token}.xlsx")

        df_summary.to_excel(summary_path, index=False)
        df_detailed_results.to_excel(detailed_path, index=False)

        # For simplicity, send summary and detailed results as separate attachments in one email
        # or combine them into a multi-sheet Excel file. For now, let's send two emails or one with two attachments
        # For this example, I'll combine into one email with two attachments by manually constructing the MIME message

        msg_facilitator = MIMEMultipart()
        msg_facilitator['From'] = SENDER_EMAIL
        msg_facilitator['To'] = ADMIN_EMAIL # Sending to admin for now, can be 'facilitator@example.com'
        msg_facilitator['Subject'] = f"Test Submission: {student_email} - {test_name}"
        msg_facilitator.attach(MIMEBase('text', 'plain', charset='utf-8'))
        msg_facilitator.get_payload()[0].set_payload(facilitator_email_body)

        for filepath in [summary_path, detailed_path]:
            with open(filepath, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filepath))
                msg_facilitator.attach(part)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg_facilitator)
            st.success(f"Test submission summary sent to {ADMIN_EMAIL}!")
        except Exception as e:
            st.error(f"Failed to send facilitator email: {e}")

        # 2. Email to Student (Questions with Correct Answers)
        student_email_body = (
            f"Dear {student_email.split('@')[0]},\n\n"
            f"Thank you for completing the '{test_name}' test. Here is a summary of your performance:\n\n"
            f"Total Questions: {summary['Total Questions']}\n"
            f"Correct Answers: {summary['Correct Answers']}\n"
            f"Incorrect Answers: {summary['Incorrect Answers']}\n"
            f"Skipped Questions: {summary['Skipped Questions']}\n"
            f"Total Marks Obtained: {summary['Total Marks Obtained']}\n"
            f"Duration Taken: {summary['Duration Taken (minutes)']:.2f} minutes\n\n"
            f"Attached is a document containing all the test questions along with the correct answers for your review.\n\n"
            f"Best regards,\nCIT Chennai Test Portal"
        )

        # Include student's detailed results in their email as well
        student_detailed_results_path = os.path.join(tmpdir, f"YourResults_{student_email.split('@')[0]}_{token}.xlsx")
        df_detailed_results.to_excel(student_detailed_results_path, index=False)


        # Create a DataFrame for questions with answers for the student
        questions_with_answers_df = questions_df.copy()
        # You might want to rename columns for clarity for the student
        questions_with_answers_df = questions_with_answers_df[['description', 'type', 'option_1', 'option_2', 'option_3', 'option_4', 'answer']]
        questions_with_answers_df.rename(columns={'description': 'Question', 'answer': 'Correct Answer'}, inplace=True)
        questions_with_answers_path = os.path.join(tmpdir, f"TestQuestions_{test_name}_{token}.csv")
        questions_with_answers_df.to_csv(questions_with_answers_path, index=False)


        msg_student = MIMEMultipart()
        msg_student['From'] = SENDER_EMAIL
        msg_student['To'] = student_email
        msg_student['Subject'] = f"Your Test Results: {test_name}"
        msg_student.attach(MIMEBase('text', 'plain', charset='utf-8'))
        msg_student.get_payload()[0].set_payload(student_email_body)

        # Attach detailed results for student
        with open(student_detailed_results_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(student_detailed_results_path))
            msg_student.attach(part)

        # Attach questions with correct answers for student
        with open(questions_with_answers_path, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(questions_with_answers_path))
            msg_student.attach(part)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg_student)
            st.success(f"Test results and questions sent to your email ({student_email})!")
        except Exception as e:
            st.error(f"Failed to send student email: {e}")


    # Clear session state for the test after submission
    if 'test_id' in st.session_state:
        del st.session_state.test_id
    if 'student_email' in st.session_state:
        del st.session_state.student_email
    if 'test_start_time' in st.session_state:
        del st.session_state.test_start_time

    go_to_page("submission_confirmation")


def submission_confirmation_page():
    """Confirms test submission and offers options."""
    st.title("Test Submitted Successfully!")
    st.markdown("---")
    st.success("Your test has been recorded. You should receive your results and the test questions via email shortly.")
    st.markdown("If you don't receive an email, please check your spam folder.")
    st.markdown("---")
    if st.button("Go to Home Page"):
        go_to_page("landing")
    st.markdown("---")


# --- Main Application Logic ---

# Initialize session state for navigation if not already set
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# Handle deep linking / URL parameters
query_params = st.query_params
if "page" in query_params:
    st.session_state.page = query_params["page"]
    if "token" in query_params:
        st.session_state.test_id = query_params["token"]
    # If a student directly accesses a test link, ensure they go through token entry first
    if st.session_state.page == "student_test" and "student_email" not in st.session_state:
        st.session_state.page = "student_token_entry"


# Page routing based on session state
if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "admin_login":
    admin_login_page()
elif st.session_state.page == "admin_dashboard":
    admin_dashboard_page()
elif st.session_state.page == "student_token_entry":
    student_token_entry_page()
elif st.session_state.page == "student_test":
    student_test_page()
elif st.session_state.page == "submission_confirmation":
    submission_confirmation_page()