# 🛍️ Google Shopping Deal Finder

**Automatically find the best deals from Google Shopping!**

This tool searches Google Shopping for discounted products and helps you discover great deals. Perfect for finding sales on electronics, fashion, home goods, and more!

You can use it in two ways:
- 🖥️ **Web Interface (Streamlit)** - Easy visual interface (recommended for beginners)
- ⌨️ **Command Line** - Quick searches from terminal

---

## 🎯 What Does This Do?

- 🔍 **Searches Google Shopping** for products on sale
- 💰 **Filters by discount** - only shows items with real savings
- 🏷️ **Category search** - find deals in specific categories like "electronics" or "fashion"
- 📊 **Shows popular searches** - see what others are looking for
- ✅ **Easy to use** - web interface or simple commands!

---

## 📋 Before You Start

You'll need:
1. **Python 3.8 or newer** installed on your computer
2. A **SERP API key** (free account available at [serpapi.com](https://serpapi.com))
3. **Supabase account** (optional, for advanced features)

---

## 🚀 Quick Start Guide

### Step 1: Install the Tool

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and run:

```bash
# Navigate to the project folder
cd google_shopping_agent

# Install required packages
pip install -r requirements.txt
```

### Step 2: Set Up Your API Keys

1. Copy the example configuration file:
   ```bash
   cp .env.example .env
   ```

2. Open the `.env` file in a text editor and add your keys:
   ```env
   SERP_API_KEY=your_serp_api_key_here
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   ```

---

## 💻 Two Ways to Use

### Option 1: Web Interface (Recommended for Beginners)

Start the web interface:

```bash
streamlit run streamlit_app.py
```

Your browser will open automatically with the interface! 🎉

**Features:**
- ✅ Visual search interface
- ✅ Filter and sort results
- ✅ Select multiple products
- ✅ Export to CSV, Excel, or JSON
- ✅ Send deals to database for approval

**How to use:**
1. Enter your search keyword (e.g., "iPhone 15")
2. Set minimum discount percentage
3. Click "Search"
4. Browse results, select products you like
5. Export or send to approval

---

### Option 2: Command Line (For Quick Searches)

Run searches directly from terminal:

```bash
python run.py --keyword "iPhone" --min-discount 15
```

This searches for iPhones with at least 15% discount!

---

## 💡 Usage Examples

### Web Interface Examples

**Start the app:**
```bash
streamlit run streamlit_app.py
```

Then use the visual interface to:
- Search for products
- Filter by discount, rating, price
- Sort results
- Export data
- Send to approval

---

### Command Line Examples

**Search for a Specific Product:**
```bash
python run.py --keyword "laptop" --min-discount 20
```
Finds laptops with at least 20% off

**Search by Category:**
```bash
python run.py --keyword "headphones" --category "electronics" --min-discount 10
```
Finds headphones in the electronics category with 10%+ discount

**Test Without Saving to Database:**
```bash
python run.py --keyword "shoes" --dry-run
```
Shows results without creating database entries (good for testing!)

**Get More Details (Verbose Mode):**
```bash
python run.py --keyword "camera" --min-discount 25 --verbose
```
Shows detailed information about what the tool is doing

---

## 🎛️ Command Line Options

| Option | What It Does | Example |
|--------|-------------|---------|
| `--keyword` | Product to search for | `--keyword "iPad"` |
| `--category` | Filter by category | `--category "electronics"` |
| `--min-discount` | Minimum discount % | `--min-discount 15` |
| `--max-queries` | How many searches to run | `--max-queries 10` |
| `--dry-run` | Test without saving | `--dry-run` |
| `--verbose` | Show detailed logs | `--verbose` |

---

## 📁 Project Structure

```
google_shopping_agent/
├── streamlit_app.py      # Web interface - run this for UI!
├── run.py                # Command line - run this for CLI!
├── agent.py              # Core search logic
├── serp_api_client.py    # Google Shopping API
├── supabase_client.py    # Database connection
├── models.py             # Data structures
├── config.py             # Configuration
├── requirements.txt      # Required packages
└── .env                  # Your API keys (create this!)
```

---

## ❓ Troubleshooting

### "No module named 'streamlit'" or similar errors
**Solution:** Run `pip install -r requirements.txt` again

### "Invalid API key" error
**Solution:** Check your `.env` file and make sure your SERP API key is correct

### Streamlit won't open in browser
**Solution:** 
- Check if port 8501 is already in use
- Try manually opening: http://localhost:8501
- Or specify a different port: `streamlit run streamlit_app.py --server.port 8502`

### No results found
**Solution:** Try:
- Lowering the `--min-discount` value
- Using more general keywords
- Removing the `--category` filter

### Tool runs but doesn't save results
**Solution:** Make sure you're not using `--dry-run` mode

---

## 🤝 Sharing with Friends

To share this tool with a friend:

1. **Send them this folder** (zip it up!)
2. **Tell them to:**
   - Install Python 3.8+ from [python.org](https://python.org)
   - Get a free SERP API key from [serpapi.com](https://serpapi.com)
   - Follow the "Quick Start Guide" above
   - Run `streamlit run streamlit_app.py` for the easy interface!

---

## 📝 Tips for Best Results

✅ **Use the web interface** - Much easier for beginners!  
✅ **Use specific keywords** - "iPhone 15 Pro" works better than just "phone"  
✅ **Try different discount levels** - Start with 10-15% for more results  
✅ **Use categories** - Helps narrow down to what you really want  
✅ **Check regularly** - Deals change daily!  

---

## 📞 Need Help?

If you run into issues:
1. Check the troubleshooting section above
2. Make sure all requirements are installed: `pip install -r requirements.txt`
3. Verify your API keys are correct in the `.env` file
4. Try the web interface first - it's easier!

---

## 📄 License

MIT License - Feel free to use and share!
