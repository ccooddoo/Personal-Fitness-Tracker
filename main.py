import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="💪 Fitness Tracker", page_icon="🔥", layout="wide")

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("fitness.db", check_same_thread=False)
    return conn

# --- DATABASE SETUP ---
def create_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY, 
                        age INTEGER, 
                        height REAL, 
                        weight REAL, 
                        password TEXT, 
                        bmi REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS workouts (
                        username TEXT, 
                        date TEXT, 
                        exercise TEXT, 
                        duration INTEGER, 
                        calories INTEGER)''')
        conn.commit()

create_db()

# --- USER AUTHENTICATION ---
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()
    return bcrypt.checkpw(password.encode(), hashed)

def register_user(username, age, height, weight, password):
    with get_db_connection() as conn:
        c = conn.cursor()
        hashed_pw = hash_password(password)
        bmi = round(weight / (height / 100) ** 2, 2)
        try:
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (username, age, height, weight, hashed_pw, bmi))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  

def login_user(username, password):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        data = c.fetchone()
        if data and verify_password(password, data[0]):
            return True
    return False

# --- WORKOUT LOGGING ---
def add_workout(username, date, exercise, duration, calories):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO workouts VALUES (?, ?, ?, ?, ?)", (username, date, exercise, duration, calories))
        conn.commit()

def load_workouts(username):
    with get_db_connection() as conn:
        return pd.read_sql_query("SELECT * FROM workouts WHERE username=?", conn, params=(username,))

# --- AI-POWERED CALORIE PREDICTION ---
def predict_calories(duration):
    X = np.array([10, 20, 30, 40, 50, 60]).reshape(-1, 1)
    y = np.array([100, 200, 300, 400, 500, 600])
    model = LinearRegression()
    model.fit(X, y)
    return round(model.predict([[duration]])[0], 2)

# --- STREAMLIT UI ---
st.sidebar.title("🏋️‍♂️ Fitness Tracker")
if "user" not in st.session_state:
    st.session_state["user"] = None  

if st.session_state["user"]:  
    menu = st.sidebar.radio("📌 Menu", ["Dashboard", "Add Workout", "Progress"])
    if st.sidebar.button("🚪 Logout"):
        st.session_state["user"] = None
        st.rerun()
else:
    menu = st.sidebar.radio("📌 Menu", ["Login", "Register"])

# --- REGISTRATION ---
if menu == "Register" and not st.session_state["user"]:
    st.subheader("🔰 Register")
    username = st.text_input("👤 Username")
    age = st.number_input("📅 Age", min_value=10, max_value=100, value=25)
    height = st.number_input("📏 Height (cm)", min_value=100, max_value=250, value=170)
    weight = st.number_input("⚖️ Weight (kg)", min_value=30, max_value=200, value=70)
    password = st.text_input("🔒 Password", type="password")
    
    if st.button("✅ Register"):
        if register_user(username, age, height, weight, password):
            st.success("🎉 Registration successful! Please log in.")
        else:
            st.error("🚨 Username already exists. Try another one.")

# --- LOGIN ---
elif menu == "Login" and not st.session_state["user"]:
    st.subheader("🔑 Login")
    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")
    
    if st.button("🔓 Login"):
        if login_user(username, password):
            st.success("✅ Login Successful! Redirecting...")
            st.session_state["user"] = username  
            st.rerun()  
        else:
            st.error("🚨 Invalid credentials. Try again.")
# --- DASHBOARD ---
elif menu == "Dashboard" and st.session_state["user"]:
    st.subheader(f"🏆 Welcome, {st.session_state['user']}! Let's achieve your fitness goals!")

    # Fetch user details
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT age, height, weight, bmi FROM users WHERE username=?", (st.session_state['user'],))
        user_data = c.fetchone()

    if user_data:
        age, height, weight, bmi = user_data
        
        # --- KPI Cards ---
        col1, col2, col3 = st.columns(3)
        col1.metric("📅 Age", age)
        col2.metric("📏 Height", f"{height} cm")
        col3.metric("⚖️ Weight", f"{weight} kg")

        # --- BMI Insights ---
        st.subheader("💡 Health Insights")
        
        # 📌 BMI Gauge Chart
        st.write("### 📊 BMI Indicator")
        fig, ax = plt.subplots(figsize=(3, 1.5))
        ax.barh(["BMI"], [bmi], color="green" if 18.5 <= bmi <= 25 else "red")
        ax.set_xlim(10, 40)
        ax.axvline(18.5, color="yellow", linestyle="dashed", label="Underweight")
        ax.axvline(25, color="yellow", linestyle="dashed", label="Overweight")
        ax.set_xlabel("BMI Value")
        st.pyplot(fig)

        # 📌 Personalized Health Recommendations
        if bmi > 25:
            st.warning("🏃 Suggested: More cardio & weight loss workouts!")
            st.info("**Tip:** Try HIIT workouts & strength training 4-5x per week.")
        elif bmi < 18.5:
            st.warning("💪 Suggested: Strength training & muscle gain workouts!")
            st.info("**Tip:** Eat high-protein meals & focus on progressive overload.")
        else:
            st.success("🎯 You have a healthy BMI! Keep going!")
            st.info("**Tip:** Maintain a balanced diet & regular activity.")

        # --- Spacing & Footer ---
        st.markdown("---")
        st.markdown("🔥 **Stay active, stay fit!** 💪")


# --- ADD WORKOUT ---
elif menu == "Add Workout" and st.session_state["user"]:
    st.subheader("🏋️ Log Your Workout")

    # Layout
    col1, col2 = st.columns(2)

    # Date & Exercise Selection
    with col1:
        date = st.date_input("📆 Workout Date", datetime.today())
        exercise = st.selectbox("🏋️ Exercise Type", ["Running", "Cycling", "Weight Training", "Yoga", "Swimming"])

    # Duration & Calories Prediction
    with col2:
        duration = st.slider("⏳ Duration (minutes)", 1, 120, 30)
        estimated_calories = predict_calories(duration)

    # 🔥 Calorie Burn Card
    st.markdown("### 🔥 Estimated Calories Burned")
    st.info(f"💪 **{estimated_calories} kcal**")

    # Workout Summary Card 📊
    st.markdown("---")
    st.markdown("### 📊 Workout Summary")
    workout_card = f"""
    🏋️ **Exercise:** {exercise}  
    ⏳ **Duration:** {duration} min  
    🔥 **Calories Burned:** {estimated_calories} kcal  
    📆 **Date:** {date.strftime('%Y-%m-%d')}
    """
    st.success(workout_card)

    # ✅ Add Workout Button with Confirmation
    if st.button("✅ Add Workout"):
        add_workout(st.session_state["user"], date, exercise, duration, estimated_calories)
        st.success("✔️ Workout Added Successfully! Keep pushing! 💪")


# --- PROGRESS ANALYSIS ---
elif menu == "Progress" and st.session_state["user"]:
    st.subheader("📊 Your Fitness Progress")
    df = load_workouts(st.session_state["user"])

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])  
        df = df.sort_values("date")  

        # 📌 Display Key Metrics in Styled Cards
        total_workouts = df.shape[0]
        total_calories = df["calories"].sum()
        avg_calories = round(df["calories"].mean(), 2)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🏋️ Total Workouts", total_workouts)
        col2.metric("🔥 Total Calories Burned", f"{total_calories} kcal")
        col3.metric("⚡ Avg Calories Per Workout", f"{avg_calories} kcal")

        # 🎯 User-defined goal for calories
        target_calories = st.sidebar.number_input("🎯 Set Your Calorie Goal", min_value=500, value=2000, step=100)

        # 📈 Line Chart - Weekly Calories Burned
        df["week"] = df["date"].dt.strftime("%Y-%U")
        weekly_summary = df.groupby("week")["calories"].sum().reset_index()

        st.write("### 📅 Weekly Calorie Burn Trend")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.lineplot(x="week", y="calories", data=weekly_summary, marker="o", color="#ff6f61", linewidth=2.5)
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.5)
        ax.set_xlabel("Week")
        ax.set_ylabel("Calories Burned")
        st.pyplot(fig)

        # 🥧 Pie Chart - Exercise Distribution with Improved Styling
        st.write("### 📌 Workout Distribution")
        pie_chart_data = df["exercise"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 6))
        colors = sns.color_palette("pastel")
        wedges, texts, autotexts = ax.pie(
            pie_chart_data, labels=pie_chart_data.index, autopct='%1.1f%%', colors=colors, textprops={'fontsize': 12}
        )
        for autotext in autotexts:
            autotext.set_color('black')
        ax.set_ylabel("")  # Remove y-axis label for clarity
        st.pyplot(fig)

        # 🔥 Heatmap - Workout Frequency (True Heatmap)
        st.write("### 🗓️ Workout Frequency Heatmap")
        df["day_of_week"] = df["date"].dt.day_name()
        heatmap_data = df["day_of_week"].value_counts().reindex(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], fill_value=0
        ).to_frame()

        fig, ax = plt.subplots(figsize=(6, 3))
        sns.heatmap(heatmap_data.T, cmap="coolwarm", annot=True, fmt="d", linewidths=1, cbar=False)
        ax.set_yticklabels(["Workouts"])
        st.pyplot(fig)

        # 🔥 Sidebar Progress Bar
        progress_value = min(1.0, total_calories / target_calories)
        st.sidebar.progress(progress_value)
        st.sidebar.write(f"🎯 **Progress Towards Goal:** {total_calories}/{target_calories} kcal")

    else:
        st.info("📉 No workout data yet. Start logging your progress!")