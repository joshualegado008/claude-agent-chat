# Start Script Improvements

**Date:** 2025-10-12
**Issues Fixed:**
1. False positive API key warnings
2. `pip: command not found` on macOS/Linux systems

## Problem

The original `start-web.sh` script was checking for `ANTHROPIC_API_KEY` only in the shell environment, which caused scary warnings even when the key was properly configured in:
- `.env` file
- `settings.json` file
- Environment variables loaded by Python

## Solution

Updated the start script to be **much smarter** about detecting API keys.

### What Changed

#### 1. Smart Multi-Source Key Detection

**Before:**
```bash
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
fi
```

**After:**
```bash
# Loads .env file automatically
# Checks if Python backend can access key from ANY source
# Only warns if TRULY missing
```

Now checks:
- ✅ Shell environment variables
- ✅ `.env` file (auto-loaded)
- ✅ `settings.json` file
- ✅ Verifies Python can actually access it

#### 2. Better Error Messages

**Before:**
```
⚠️  Warning: ANTHROPIC_API_KEY not set
   Set it with: export ANTHROPIC_API_KEY='sk-ant-...'
```

**After:**
```
⚠️  Warning: ANTHROPIC_API_KEY not found in:
   • Shell environment ($ANTHROPIC_API_KEY)
   • .env file
   • settings.json

   Configure with one of these methods:
   1. export ANTHROPIC_API_KEY='sk-ant-...'
   2. Create .env file: echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
   3. Run settings menu: python3 coordinator_with_memory.py

   Continue anyway? [y/N]:
```

Now:
- Shows ALL places it checked
- Gives multiple configuration options
- Asks for confirmation before continuing
- Only shows if key is ACTUALLY missing

#### 3. Backend Health Check

**Before:**
```bash
sleep 3  # Just wait blindly
```

**After:**
```bash
# Actually checks if backend is responding
for i in {1..15}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done
```

Now:
- Polls backend health endpoint
- Shows progress every 5 seconds
- Warns if backend takes too long
- More reliable startup detection

#### 4. Smarter Dependency Installation

**Before:**
```bash
pip install -r requirements-web.txt > /dev/null 2>&1  # Always silent
```

**After:**
```bash
# Shows output on first run, silent after
if [ ! -f ".installed" ]; then
    echo "📦 Installing backend dependencies (first run)..."
    pip install -r requirements-web.txt
    touch .installed
else
    pip install -r requirements-web.txt > /dev/null 2>&1
fi
```

Now:
- Shows progress on first run (when you care)
- Silent on subsequent runs (less noise)
- Uses `.installed` marker file

## Usage

Just run as before:

```bash
./web/start-web.sh
```

You'll now see:

**If key is found:**
```
🔑 Checking API key configuration...
✅ API key configured and accessible
```

**If key is missing:**
```
🔑 Checking API key configuration...
⚠️  Warning: ANTHROPIC_API_KEY not found in:
   • Shell environment ($ANTHROPIC_API_KEY)
   • .env file
   • settings.json

   Configure with one of these methods:
   1. export ANTHROPIC_API_KEY='sk-ant-...'
   2. Create .env file: echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
   3. Run settings menu: python3 coordinator_with_memory.py

   Continue anyway? [y/N]:
```

## Benefits

1. ✅ **No false warnings** - Only warns when key is truly missing
2. ✅ **Auto-loads .env** - No need to manually export variables
3. ✅ **Better UX** - Clear, actionable error messages
4. ✅ **Reliable startup** - Health checks ensure backend is ready
5. ✅ **Less noise** - Quiet on subsequent runs

## Testing

Try these scenarios:

```bash
# Scenario 1: Key in environment (should work)
export ANTHROPIC_API_KEY='sk-ant-...'
./web/start-web.sh
# → Should see: ✅ API key configured and accessible

# Scenario 2: Key in .env file (should work)
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
./web/start-web.sh
# → Should see: ✅ API key configured and accessible

# Scenario 3: Key in settings.json (should work)
# (Configure via: python3 coordinator_with_memory.py → Settings)
./web/start-web.sh
# → Should see: ✅ API key configured and accessible

# Scenario 4: No key anywhere (should warn)
unset ANTHROPIC_API_KEY
rm .env
rm settings.json
./web/start-web.sh
# → Should see warning and prompt to continue
```

#### 5. Python/Pip Command Compatibility

**Problem:** Script used `pip` which doesn't exist on macOS (uses `pip3`)

**Solution:** Added smart pip detection that tries multiple commands:

```bash
# Function tries in order:
1. python3 -m pip  (most reliable)
2. pip3            (common on macOS/Linux)
3. pip             (Windows, older systems)
```

Now works on:
- ✅ macOS (uses `python3 -m pip`)
- ✅ Linux (uses `pip3` or `python3 -m pip`)
- ✅ Windows (uses `pip`)
- ✅ Virtual environments (respects active venv)

Also consistently uses `python3` instead of `python` throughout.

## Files Modified

- `web/start-web.sh` - Main improvements (pip detection, health checks, key detection)
- `.gitignore` - Added `web/backend/.installed` marker

## Backward Compatibility

✅ **Fully backward compatible** - All existing configurations still work
✅ **No breaking changes** - Just better detection and messaging
✅ **Terminal interface unaffected** - Completely separate

---

**Result:** Much more reliable startup script with better user experience! 🎉
