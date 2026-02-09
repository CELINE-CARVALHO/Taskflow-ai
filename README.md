# 📊 AI-Powered Live Dashboard

> **Privacy-first, schema-agnostic work dashboard that dynamically interprets any spreadsheet**

## 🌟 What Makes This Special

Most dashboards assume:
- ✅ Fixed schemas
- ✅ Stable columns  
- ✅ Stored data

**This app assumes:**
- ❌ Chaos
- ❌ Change
- ❌ Privacy constraints

**And still works perfectly.**

## 🚀 Quick Start

### 1. Run the PowerShell script to create structure:
```powershell
.\create_structure.ps1
cd ai-dashboard-app
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure your API key in `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=mixtral-8x7b-32768
```

Get your free Groq API key at: https://console.groq.com

### 4. Run the application:
```bash
streamlit run app.py
```

## 📖 How to Use

1. Open the app (automatically opens at http://localhost:8501)
2. Enter your name in the sidebar
3. Choose data source:
   - **Google Sheets**: Paste public sheet URL
   - **Excel File**: Upload .xlsx file
4. Click "Load Dashboard"
5. View your personalized dashboard
6. Ask questions in natural language

## 🧠 AI Agents

The system uses 4 specialized AI agents:

1. **Sheet Classifier** - Identifies relevant sheets
2. **Column Interpreter** - Maps columns to concepts
3. **Dashboard Builder** - Designs optimal layouts
4. **Question Interpreter** - Answers your questions

## 🔒 Privacy Guarantee

- ❌ No database
- ❌ No cache
- ❌ No logs
- ✅ 100% ephemeral

## 🧪 Test with Sample Data

Use the included `complex_work_tracker.xlsx` to test all features.

## 📞 Need Help?

Check the troubleshooting section in the full README or open an issue on GitHub.

---

**Built with privacy-first principles**