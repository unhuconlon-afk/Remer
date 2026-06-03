# Google Calendar API Setup Guide for Public Users

To use the Calendar Assistant, you need to set up Google Calendar OAuth credentials to authorize the app to sync events to your Google Calendar. Follow these step-by-step instructions.

---

## 🛠️ Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Log in with your Google Account.
3. In the top-left corner, click the project drop-down menu and select **New Project**.
4. Give your project a name (e.g., `My Calendar Assistant`) and click **Create**.

---

## 🔌 Step 2: Enable the Google Calendar API
1. In the Google Cloud Console search bar at the top, type **Google Calendar API** and click on it.
2. Click the blue **Enable** button to activate the API for your project.

---

## 🔒 Step 3: Configure the OAuth Consent Screen
Before generating credentials, you must configure how the authentication screen looks:
1. In the left sidebar, navigate to **APIs & Services** > **OAuth consent screen**.
2. For **User Type**, choose **External** and click **Create**.
3. Fill in the required fields:
   - **App name**: `Calendar Assistant`
   - **User support email**: (Your Gmail address)
   - **Developer contact information**: (Your Gmail address)
4. Click **Save and Continue**.
5. **Scopes Screen**: Click **Save and Continue** (no custom scopes needed here).
6. **Test Users Screen**: Click **+ Add Users** and type your own Gmail address. *(This is required since the app is in "Testing" mode and only approved test users can log in).*
7. Click **Save and Continue** to finish.

---

## 🔑 Step 4: Create & Download OAuth Credentials
1. In the left sidebar, click **Credentials**.
2. Click **+ Create Credentials** at the top and select **OAuth client ID**.
3. Set the **Application type** to **Desktop app**.
4. Set the name to `Calendar Assistant Desktop` and click **Create**.
5. A pop-up will show "OAuth client created". Click **Download JSON** on the right side of the screen.
6. Rename the downloaded file to exactly **`credentials.json`** and place it in your project's root folder (`remer/`).

---

## 🚀 Step 5: Authorize the App (First Run Only)
1. Open PowerShell / Command Prompt and run:
   ```powershell
   py -3.12 calendar_syncer.py
   ```
2. A browser window will pop up asking you to sign in with your Google Account.
3. Choose the account you added to **Test Users** in Step 3.
4. Click **Continue** (if Google warns that the app isn't verified yet — this is normal since it's your own private app) and then click **Allow**.
5. Once authorization is complete, a `token.json` file is saved. Your setup is now complete!
