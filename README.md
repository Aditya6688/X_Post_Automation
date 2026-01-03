# X Automate - AI-Powered Twitter Content Generator

An automated content generation tool that fetches trending tech content from multiple sources, generates engaging Twitter/X thread hooks using AI, and saves them to your Notion database for easy review and publishing.

## 🚀 Features

- **Multi-Source Content Fetching**: Automatically pulls content from:
  - GitHub Trending (Python repositories)
  - HackerNews (Tech news)
  - Dev.to (Engineering tutorials)
  - ArXiv (AI research papers)

- **AI-Powered Tweet Generation**: Uses OpenAI GPT models to create context-aware tweet drafts with different personas:
  - **Code**: Pragmatic engineer perspective
  - **Research**: AI researcher breaking down complex papers
  - **Tutorial**: Helpful mentor sharing learning resources
  - **News**: Tech commentator with insightful takes

- **Smart Content Selection**: Weighted random selection ensures variety (40% Code, 30% News, 20% Research, 10% Tutorials)

- **Notion Integration**: Automatically saves drafts to your Notion database with metadata (title, draft, source URL, type)

- **One Draft Per Run**: Generates a single high-quality draft per execution to maintain focus

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Notion API token ([Create integration](https://www.notion.so/my-integrations))
- Notion database with the following properties:
  - `Name` (Title)
  - `Tweet Draft` (Rich Text)
  - `Source URL` (URL)
  - `Status` (Status) - with "Not started" option
  - `Type` (Select) - with options: "Code", "News", "Research", "Tutorial"

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/X_Automate.git
   cd X_Automate
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv myenv
   
   # On Windows
   myenv\Scripts\activate
   
   # On macOS/Linux
   source myenv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

1. **Create a `.env` file** in the project root:
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   NOTION_TOKEN=secret_your-notion-token-here
   NOTION_DB_ID=your-notion-database-id-here
   ```

2. **Get your Notion Database ID**:
   - Open your Notion database in a browser
   - The URL will look like: `https://www.notion.so/workspace/your-database-id?v=...`
   - Copy the database ID (the long string of characters before the `?`)

3. **Set up your Notion database**:
   - Create a new database or use an existing one
   - Add the required properties mentioned in Prerequisites
   - Share the database with your Notion integration

## 🎯 Usage

Simply run the script:

```bash
python ghostwriter.py
```

The script will:
1. Randomly select a content source based on weights
2. Fetch the top 3 items from that source
3. Randomly pick one item
4. Generate an AI-powered tweet draft
5. Save it to your Notion database

### Example Output

```
--- 🎲 Rolling the Dice for Content Source ---
📡 Source selected: GitHub Trending...
✅ Selected Winner: Repo: username/repo-name - A cool project description
🧠 Generating draft...
🚀 Success! 1 Draft saved to Notion.
```

## 📁 Project Structure

```
X_Automate/
├── ghostwriter.py      # Main script
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── README.md          # This file
└── myenv/             # Virtual environment (gitignored)
```

## 🔧 Customization

### Adjust Source Weights

Edit the weights in `run_ghostwriter_v2()` function:

```python
weights = [0.4, 0.3, 0.2, 0.1]  # GitHub, News, Research, Tutorial
```

### Change AI Model

Modify the model in `generate_tweet()` function:

```python
model="gpt-5-nano-2025-08-07"  # Change to your preferred model
```

### Modify Personas

Edit the persona prompts in `generate_tweet()` to match your voice and style.

## 🐛 Troubleshooting

- **"Missing API Keys" error**: Ensure your `.env` file exists and contains all three required variables
- **Notion save errors**: Verify your database properties match the required names and types
- **Import errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`
- **Status option errors**: Ensure "Not started" exists as a status option in your Notion database

## 📝 License

This project is open source and available under the [MIT License].

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Aditya6688/X_Post_Automation/issues).

## ⚠️ Disclaimer

This tool generates draft content. Always review and edit the generated tweets before publishing to ensure they align with your brand voice and comply with platform guidelines.

## 📧 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Made with ❤️ for content creators who want to automate their Twitter/X workflow**

