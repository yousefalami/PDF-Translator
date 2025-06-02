# PDF Translator

This project allows you to translate PDF files into other languages using the [WebAI to API](https://github.com/Amm1rr/WebAI-to-API/) service. The script extracts the text from each page of a PDF and sends it to your [WebAI to API](https://github.com/Amm1rr/WebAI-to-API/) server for translation. The final result is saved in a Word (.docx) file with two columns: the original text and the translated text.

This project is especially useful for students, researchers, translators, and anyone who needs to quickly and efficiently translate PDF documents.

## ⚙️ 1. Check the Configuration File

Open the `config.ini` file and adjust the settings if needed.

> **Note:** The default settings are pre-configured. If you are running [WebAI to API](https://github.com/Amm1rr/WebAI-to-API/) with the same configuration, you do not need to change anything.

---

## 🧰 2. Prerequisites

Before running the project, make sure the following are installed:

- **Python 3.10 or higher** (version 3.13 is currently used)
- **Poetry** (for dependency management)

### ✅ Installing Poetry

#### For **Linux** or **macOS** users:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### For **Windows** users:

1. Visit the following address:

   [https://install.python-poetry.org](https://install.python-poetry.org)

2. Run the installer script using Python. For example, in PowerShell, enter:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

3. After installation, you may need to add the following path to your `PATH` environment variable:

```
%USERPROFILE%\AppData\Roaming\Python\Scripts
```

> To confirm the installation, run `poetry --version` in your terminal.

---

## 📋 3. Install Dependencies

Once the prerequisites are installed, navigate to the project directory and run:

```bash
poetry install
```

---

## ▶️ 4. Run the Program

To run the main script, use the following command:

```bash
poetry run python main.py
```

#### Credit:

[Github](https://github.com/amm1rr/) | [Twitter](https://x.com/M_Khani65/)

### 📄 License

This project is released under the MIT License. Feel free to modify and use it.

2025
