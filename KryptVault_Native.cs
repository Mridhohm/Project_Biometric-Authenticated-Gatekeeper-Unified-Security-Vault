using System;
using System.IO;
using System.Diagnostics;
using System.Net;
using System.Threading;
using System.Windows.Forms;

namespace KryptVault
{
    static class Program
    {
        private const int Port = 8501;
        private static readonly string AppUrl = "http://localhost:" + Port;

        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string appDir = Path.Combine(baseDir, "geovault-crypto-app");
                if (!Directory.Exists(appDir) && File.Exists(Path.Combine(baseDir, "app.py")))
                {
                    appDir = baseDir;
                }
                else if (!Directory.Exists(appDir))
                {
                    string sub = Path.Combine(baseDir, "Project_Biometric-Authenticated-Gatekeeper-Unified-Security-Vault-main", "geovault-crypto-app");
                    if (Directory.Exists(sub)) appDir = sub;
                }

                if (!File.Exists(Path.Combine(appDir, "app.py")))
                {
                    MessageBox.Show(
                        "Direktori aplikasi Krypt Vault tidak ditemukan.\nPastikan berkas app.py berada dalam folder geovault-crypto-app.",
                        "Krypt Vault - Kesalahan",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                string pythonPath = FindPython();
                if (string.IsNullOrEmpty(pythonPath))
                {
                    MessageBox.Show(
                        "Python 3 tidak ditemukan di sistem ini.\nSilakan instal Python 3.10+ (centang 'Add Python to PATH') untuk menjalankan Krypt Vault.",
                        "Krypt Vault - Kebutuhan Sistem",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    );
                    return;
                }

                string browserPath = FindBrowser();

                ProcessStartInfo serverPsi = new ProcessStartInfo();
                serverPsi.FileName = pythonPath;
                serverPsi.Arguments = string.Format(
                    "-m streamlit run app.py --server.port {0} --server.headless true --browser.serverAddress localhost --server.enableCORS false --server.enableXsrfProtection false",
                    Port
                );
                serverPsi.WorkingDirectory = appDir;
                serverPsi.CreateNoWindow = true;
                serverPsi.UseShellExecute = false;
                serverPsi.WindowStyle = ProcessWindowStyle.Hidden;

                Process serverProcess = null;
                try
                {
                    serverProcess = Process.Start(serverPsi);
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        "Gagal memulai server internal Krypt Vault:\n" + ex.Message,
                        "Krypt Vault - Kesalahan",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                bool ready = WaitForServer(AppUrl, 25);
                if (!ready)
                {
                    KillProcessTree(serverProcess);
                    MessageBox.Show(
                        "Server internal tidak merespons dalam waktu yang ditentukan.\nPastikan port 8501 tidak terblokir oleh firewall lokal.",
                        "Krypt Vault - Waktu Habis",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                Process browserProcess = null;
                if (!string.IsNullOrEmpty(browserPath))
                {
                    ProcessStartInfo browserPsi = new ProcessStartInfo();
                    browserPsi.FileName = browserPath;
                    browserPsi.Arguments = string.Format("--app={0} --window-size=1300,880", AppUrl);
                    browserPsi.UseShellExecute = false;
                    browserProcess = Process.Start(browserPsi);
                }
                else
                {
                    Process.Start(AppUrl);
                }

                if (browserProcess != null)
                {
                    browserProcess.WaitForExit();
                }
                else if (serverProcess != null)
                {
                    serverProcess.WaitForExit();
                }

                KillProcessTree(serverProcess);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Terjadi kesalahan pada aplikasi Krypt Vault:\n" + ex.Message,
                    "Krypt Vault",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }

        private static string FindPython()
        {
            string pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
            string[] paths = pathEnv.Split(Path.PathSeparator);
            foreach (string p in paths)
            {
                try
                {
                    string candidate = Path.Combine(p.Trim(), "python.exe");
                    if (File.Exists(candidate)) return candidate;
                }
                catch { }
            }

            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] directCandidates = new string[]
            {
                @"C:\Python314\python.exe",
                @"C:\Python313\python.exe",
                @"C:\Python312\python.exe",
                @"C:\Python311\python.exe",
                @"C:\Python310\python.exe",
                Path.Combine(localAppData, @"Programs\Python\Python314\python.exe"),
                Path.Combine(localAppData, @"Programs\Python\Python313\python.exe"),
                Path.Combine(localAppData, @"Programs\Python\Python312\python.exe"),
                Path.Combine(localAppData, @"Programs\Python\Python311\python.exe"),
                Path.Combine(localAppData, @"Programs\Python\Python310\python.exe")
            };

            foreach (string c in directCandidates)
            {
                if (File.Exists(c)) return c;
            }

            return null;
        }

        private static string FindBrowser()
        {
            string progFiles86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
            string progFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);

            string[] candidates = new string[]
            {
                Path.Combine(progFiles86, @"Microsoft\Edge\Application\msedge.exe"),
                Path.Combine(progFiles, @"Microsoft\Edge\Application\msedge.exe"),
                Path.Combine(progFiles, @"Google\Chrome\Application\chrome.exe"),
                Path.Combine(progFiles86, @"Google\Chrome\Application\chrome.exe"),
                Path.Combine(localAppData, @"Google\Chrome\Application\chrome.exe"),
                Path.Combine(localAppData, @"Microsoft\Edge\Application\msedge.exe")
            };

            foreach (string c in candidates)
            {
                if (File.Exists(c)) return c;
            }

            return null;
        }

        private static bool WaitForServer(string url, int timeoutSeconds)
        {
            DateTime start = DateTime.Now;
            while ((DateTime.Now - start).TotalSeconds < timeoutSeconds)
            {
                try
                {
                    HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
                    request.Timeout = 1000;
                    request.Method = "GET";
                    using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    {
                        if (response.StatusCode == HttpStatusCode.OK)
                            return true;
                    }
                }
                catch
                {
                    Thread.Sleep(500);
                }
            }
            return false;
        }

        private static void KillProcessTree(Process p)
        {
            if (p == null) return;
            try
            {
                if (p.HasExited) return;
            }
            catch { return; }

            try
            {
                ProcessStartInfo psi = new ProcessStartInfo("taskkill", string.Format("/F /T /PID {0}", p.Id));
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                Process killProc = Process.Start(psi);
                if (killProc != null) killProc.WaitForExit(2000);
            }
            catch
            {
                try { p.Kill(); } catch { }
            }
        }
    }
}
