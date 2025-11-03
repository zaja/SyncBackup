# SyncBackup v1.3 - User Manuals

This directory contains user manuals for SyncBackup application.

## Available Manuals

- **Main Documentation**: See [../README.md](../README.md) for complete documentation
- **Quick Start Guide**: See [../QUICK_START_v1.3.md](../QUICK_START_v1.3.md)
- **Changelog**: See [../CHANGES_v1.3.md](../CHANGES_v1.3.md)
- **Release Notes**: See [../RELEASE_NOTES_v1.3.md](../RELEASE_NOTES_v1.3.md)

## New Features in v1.3

### 🔔 Smart Notification Batching
- **Batch Mode** (Default): Groups notifications and shows summary every 5 minutes
- **Immediate Mode**: Shows notifications instantly
- **Disabled Mode**: No notifications

### ⚙️ Settings Tab
- Language selection (Croatian/English)
- Notification mode configuration
- Batch interval settings (60-3600 seconds)
- Windows Service management

### 🔧 Windows Service Support
- Run as Windows Service for background operation
- Auto-start with Windows
- Install/Uninstall/Status management from GUI
- Requires pywin32: `pip install pywin32`

## Quick Links

- **Repository**: https://github.com/zaja/SyncBackup
- **Website**: https://svejedobro.hr
- **Author**: Goran Zajec

## Language Support

The application now supports multiple languages:
- English (en)
- Croatian (hr)

Users can add new languages by creating JSON files in `app/languages/` directory.

## Getting Help

For detailed instructions, troubleshooting, and examples, please refer to the main README.md file in the root directory.
