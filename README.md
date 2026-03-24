# DataLytiq 📊

DataLytiq is an interactive data application built with Python Shiny. It provides a seamless interface for uploading, cleaning, transforming, and analyzing datasets.

---

## 🚀 Overview

DataLytiq is designed to help users quickly explore and process datasets without writing extensive code. The app integrates multiple stages of a typical data science workflow:

- Data Upload
- Data Cleaning
- Feature Engineering
- Exploratory Data Analysis (EDA)

It supports multiple data formats and provides real-time updates as users interact with the interface.

---

## 📂 Features

### 1. Data Upload
- Upload datasets in **CSV, Excel, or JSON** format
- Or use a built-in sample dataset (Iris) for quick testing
- Preview uploaded data instantly

---

### 2. Data Cleaning
- Remove duplicate rows
- Handle missing values
- Standardize formats
- Detect and manage outliers
- View before vs after statistics

---

### 3. Feature Engineering
- Apply mapping to numerical fields
- Perform binning on continuous data
- One-hot encode categorical fields
- Log transform numerical fields

---

### 4. Exploratory Data Analysis (EDA)
- Generate numerical summary tables
- Analyze categorical distributions
- Create visualizations for deeper insights
- Export processed results as CSV

---

## 🛠️ Project Structure
```
DataLytiq/
│
├── app.py # Main Shiny app entry point
├── README.md
├── iris_data.csv # Built-in sample dataset
│
└── modules/
├── data_loader.py # Load datasets (CSV, Excel, JSON)
├── cleaning.py # Data cleaning functions
├── feature_engineering.py # Feature transformations
├── eda.py # Exploratory analysis
```


---

## ⚙️ Installation

Make sure you have Python 3.10+ installed.

Install required packages:

```bash
pip install shiny pandas numpy matplotlib seaborn
```

---
## 🚀 Running the App

### 🌐 Option 1: Use Online (Recommended)
Access the deployed application directly in your browser:

👉 https://yourname.shinyapps.io/DataLytiq



### 💻 Option 2: Run Locally

Navigate to the project directory:

```bash
cd Stats-5243-project-2
```
Run the Shiny app:
```bash
shiny run --reload app.py
```
Then open your browser and go to:
```
http://127.0.0.1:8000
```
---
## 🧪 Example Usage

1. Go to the **Upload** tab  
2. Upload your dataset or click **Use Sample Dataset (Iris)**  
3. Navigate to:
   - **Cleaning** → preprocess data  
   - **Feature Engineering** → create new variables  
   - **EDA** → explore insights  
4. Download processed data if needed
---

## ⚠️ Notes
- Large datasets may impact performance depending on system resources.
---

## 👥 Team Members
- Yao Ouyang – App architecture & data upload
- Qiujun Zhang - Data cleaning module
- Zhonghao Liu - Feature engineering module
- Crystal Guo - EDA module

---
## 📌 Main Technologies Used
- Python
- Shiny for Python
---
## 📄 License
This project is for academic use (STATGR5243 Project 2).
