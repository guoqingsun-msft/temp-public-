import requests
import os
import time
from datetime import datetime
import urllib3

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set environment variable for requests to use an empty CA bundle
os.environ["REQUESTS_CA_BUNDLE"] = ""

# ========== CONFIGURATION ==========
BASE_OUTPUT_FOLDER = r"C:\ctemp\PowerBI_Backups"
POWER_BI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
BASE_URL = "https://api.powerbi.com/v1.0/myorg"

# Module-level OUTPUT_FOLDER default so helper functions can reference it
OUTPUT_FOLDER = BASE_OUTPUT_FOLDER
# List of workspace IDs to export from. MUST be specified - script will not run without this!
# Example: ["856755d4-27a3-474d-b2e6-385b151d407d", "c2e96de6-f2b6-417b-b5e5-21750327d6a5", "another-id"]
WORKSPACE_IDS = [
    "c4cdb75f-3b13-41b4-96b0-7d5ab19d684b",
    "8bc62fc9-a7af-4b1d-9c89-3f764ceddbf8",
    "856755d4-27a3-474d-b2e6-385b151d407d",
]

# Set to True if you are a Power BI Admin and want to export from ALL workspaces
# This uses Admin APIs which require Fabric/Power BI Admin role
USE_ADMIN_API = False


# ========== AUTHENTICATION ==========
def get_access_token():
    """Authenticate using interactive browser login"""
    from azure.identity import InteractiveBrowserCredential
    import ssl

    print("🔐 Opening browser for authentication...")

    # Create SSL context that doesn't verify certificates
    ssl_context = ssl._create_unverified_context()

    credential = InteractiveBrowserCredential()
    token = credential.get_token(POWER_BI_SCOPE)
    print("✅ Authentication successful!")
    return token.token


# ========== HELPER FUNCTIONS ==========
def sanitize_filename(name):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    return name.strip()


def format_size(size_bytes):
    """Format bytes to human readable size"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


# ========== API FUNCTIONS ==========
def get_workspaces(headers):
    """Get specified workspaces from WORKSPACE_IDS list"""
    # Validate that WORKSPACE_IDS is specified
    if not WORKSPACE_IDS:
        print("\n❌ ERROR: WORKSPACE_IDS list is empty!")
        print(
            "   Please specify at least one workspace ID in the WORKSPACE_IDS configuration."
        )
        print("   The script will not run without a filtered list of workspaces.")
        raise ValueError("WORKSPACE_IDS must be specified")

    # Regular API - gets only workspaces user has access to
    url = f"{BASE_URL}/groups"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    all_workspaces = response.json().get("value", [])

    # Filter to specified workspaces only
    filtered = [ws for ws in all_workspaces if ws["id"] in WORKSPACE_IDS]

    if not filtered:
        print(
            f"\n❌ ERROR: None of the specified workspace IDs were found or accessible."
        )
        print(f"   Specified IDs: {WORKSPACE_IDS}")
        print(f"   Available workspaces: {[ws['id'] for ws in all_workspaces]}")
        raise ValueError("No workspaces found matching WORKSPACE_IDS")

    return filtered


def get_reports_in_workspace(headers, workspace_id):
    url = f"{BASE_URL}/groups/{workspace_id}/reports"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("value", [])


def export_report(headers, workspace_id, report_id, report_name, workspace_name):
    """
    Export a report as .pbix file

    downloadType options:
    - IncludeModel: Export with data (for Import mode reports)
    - LiveConnect: Export with live connection (no data)

    preferClientRouting=true: Workaround for timeout issues with large files
    """
    # Try first without downloadType parameter (simpler request)
    # If that fails, try with IncludeModel
    urls_to_try = [
        f"{BASE_URL}/groups/{workspace_id}/reports/{report_id}/Export",
        f"{BASE_URL}/groups/{workspace_id}/reports/{report_id}/Export?downloadType=IncludeModel&preferClientRouting=true",
    ]

    last_error = None
    for url in urls_to_try:
        try:
            response = requests.get(
                url, headers=headers, stream=True, timeout=1800
            )  # 30 min timeout

            if response.status_code == 200:
                # Create workspace folder
                workspace_folder = os.path.join(
                    OUTPUT_FOLDER, sanitize_filename(workspace_name)
                )
                os.makedirs(workspace_folder, exist_ok=True)

                # Save the file
                file_path = os.path.join(
                    workspace_folder, f"{sanitize_filename(report_name)}.pbix"
                )

                total_size = 0
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        total_size += len(chunk)

                return file_path, total_size, None

            elif response.status_code == 404:
                error_detail = (
                    response.text[:300] if response.text else "Report not found"
                )
                last_error = f"404 Not Found: {error_detail}"
            elif response.status_code == 403:
                error_detail = response.text[:300] if response.text else "Access denied"
                last_error = f"403 Forbidden: {error_detail}"
            elif response.status_code == 429:
                last_error = "Rate limited - too many requests"
            else:
                error_msg = response.text[:300] if response.text else "Unknown error"
                last_error = f"HTTP {response.status_code}: {error_msg}"

        except requests.exceptions.Timeout:
            last_error = "Request timed out - file may be too large"
        except requests.exceptions.RequestException as e:
            last_error = f"Request error: {str(e)}"

    return None, 0, last_error


# ========== MAIN EXPORT FUNCTION ==========
def bulk_export_all_reports():
    """Main function to export reports from specified workspaces"""

    # Ensure helper functions use the same OUTPUT_FOLDER variable
    global OUTPUT_FOLDER

    # Create timestamped output folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    OUTPUT_FOLDER = os.path.join(BASE_OUTPUT_FOLDER, f"PBIX_Backup_{timestamp}")

    print("=" * 60)
    print("Power BI Bulk Report Export Tool")
    print("=" * 60)
    print(f"Workspaces to export: {len(WORKSPACE_IDS)}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Authenticate
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Get all workspaces
    print("\n📂 Fetching workspaces...")
    workspaces = get_workspaces(headers)
    print(f"   Found {len(workspaces)} workspaces")

    # Results tracking
    results = {"success": [], "failed": [], "skipped": []}
    total_size = 0

    # Process each workspace
    for i, workspace in enumerate(workspaces, 1):
        workspace_id = workspace["id"]
        workspace_name = workspace["name"]

        print(f"\n{'─'*60}")
        print(f"📁 [{i}/{len(workspaces)}] Workspace: {workspace_name}")
        print(f"   ID: {workspace_id}")

        try:
            reports = get_reports_in_workspace(headers, workspace_id)
            print(f"   📊 Found {len(reports)} reports")

            if not reports:
                continue

            for j, report in enumerate(reports, 1):
                report_id = report["id"]
                report_name = report["name"]
                report_type = report.get("reportType", "PowerBIReport")

                # Skip paginated reports (RDL) - cannot export as .pbix
                if report_type == "PaginatedReport":
                    print(
                        f"      ⏭️  [{j}/{len(reports)}] Skipping (Paginated): {report_name}"
                    )
                    results["skipped"].append(
                        {
                            "workspace": workspace_name,
                            "report": report_name,
                            "reason": "Paginated report (RDL)",
                        }
                    )
                    continue

                print(
                    f"      📥 [{j}/{len(reports)}] Exporting: {report_name}...",
                    end=" ",
                    flush=True,
                )

                file_path, file_size, error = export_report(
                    headers, workspace_id, report_id, report_name, workspace_name
                )

                if file_path:
                    print(f"✅ ({format_size(file_size)})")
                    results["success"].append(
                        {
                            "workspace": workspace_name,
                            "report": report_name,
                            "path": file_path,
                            "size": file_size,
                        }
                    )
                    total_size += file_size
                else:
                    print(f"❌")
                    print(f"         Error: {error}")
                    results["failed"].append(
                        {
                            "workspace": workspace_name,
                            "report": report_name,
                            "error": error,
                        }
                    )

                # Delay to avoid throttling (429 errors)
                time.sleep(2)

        except requests.exceptions.HTTPError as e:
            print(f"   ❌ Error accessing workspace: {e}")
            results["failed"].append(
                {
                    "workspace": workspace_name,
                    "report": "(all reports)",
                    "error": str(e),
                }
            )
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            results["failed"].append(
                {
                    "workspace": workspace_name,
                    "report": "(all reports)",
                    "error": str(e),
                }
            )

    # Print summary
    print("\n" + "=" * 60)
    print("EXPORT SUMMARY")
    print("=" * 60)
    print(f"✅ Successful exports: {len(results['success'])}")
    print(f"❌ Failed exports: {len(results['failed'])}")
    print(f"⏭️  Skipped: {len(results['skipped'])}")
    print(f"📦 Total size downloaded: {format_size(total_size)}")
    print(f"📂 Output folder: {OUTPUT_FOLDER}")
    print(f"⏱️  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # List failures if any
    if results["failed"]:
        print("\n" + "─" * 60)
        print("FAILED EXPORTS:")
        for item in results["failed"]:
            print(f"  • {item['workspace']}/{item['report']}")
            print(f"    Error: {item['error']}")

    # Save log file
    log_file = os.path.join(
        OUTPUT_FOLDER, f"export_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("Power BI Export Log\n")
        f.write("=" * 60 + "\n\n")

        f.write("SUCCESSFUL:\n")
        for item in results["success"]:
            f.write(
                f"  {item['workspace']}/{item['report']} ({format_size(item['size'])})\n"
            )

        f.write("\nFAILED:\n")
        for item in results["failed"]:
            f.write(f"  {item['workspace']}/{item['report']}: {item['error']}\n")

        f.write("\nSKIPPED:\n")
        for item in results["skipped"]:
            f.write(f"  {item['workspace']}/{item['report']}: {item['reason']}\n")

    print(f"\n📝 Log saved to: {log_file}")

    return results


# ========== ENTRY POINT ==========
if __name__ == "__main__":
    try:
        bulk_export_all_reports()
    except KeyboardInterrupt:
        print("\n\n⚠️ Export cancelled by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise
