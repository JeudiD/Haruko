# ✅ How I Got My Discord Bot Running in the Background (Windows)

## 🔨 Goal:
Keep the bot running even when all windows (VSCode, terminals, etc.) are closed — and **start automatically on boot**.

## 🔧 Tools Used:
- [nssm](https://nssm.cc/) – Non-Sucking Service Manager (runs scripts as background Windows services)
- Python 3.13
- `bot.py` – your main bot file

## 🪛 Steps Taken:

1. **Install NSSM**  
   Downloaded and extracted from: [https://nssm.cc/download](https://nssm.cc/download)  
   (You used: `C:\Users\Dale\Downloads\nssm-2.24\nssm-2.24\win64`)

2. **Open PowerShell as Admin**  
   `Start > PowerShell > Run as Administrator`

3. **Navigate to NSSM Folder**  
   ```powershell
   cd "C:\Users\Dale\Downloads\nssm-2.24\nssm-2.24\win64"
   ```

4. **Create a Windows Service**  
   ```powershell
   .\nssm.exe install NingyoBot
   ```

5. **In the NSSM GUI**, fill in:
   - **Path**:  
     `C:\Users\Dale\AppData\Local\Programs\Python\Python313\python.exe`
   - **Arguments**:  
     `bot.py`
   - **Startup directory**:  
     `C:\Users\Dale\DiscordBot`

6. **Click OK / Save**

7. **Start the Service** (optional if it didn’t auto-start):
   ```powershell
   nssm start NingyoBot
   ```

## 💡 Result:

- Your bot now runs in the **background**.
- No terminal or editor needs to be open.
- It **starts automatically when you boot up your PC**.
- Can be managed in **Task Manager > Services** or via:
  ```powershell
  nssm stop NingyoBot
  nssm restart NingyoBot
  ```

