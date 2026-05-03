# JS8Spotter DB Update Tool, MIT License, Joe Lyman KF7MIX
# You should have received a copy of the source and license with the program

# UPGRADE Notes:

* The upgrade process is simple and quick, but you need to read/understand it first
* Do NOT overwrite your old files with the new files. You can test your upgrade BEFORE replacing
  your working installation
* READ the PDF manual, this file, and the dbtool text file before starting
* ALWAYS BACKUP your files, especially your js8spotter.db file BEFORE attempting an upgrade


# Database Update Process

Step 1: Make a backup of your js8spotter.db file.
        This file contains all of your user data, including profiles, keywords, and all captured
        activity. You should regularly backup this file, if the contents are important to you.

Step 2: Get the latest version of JS8Spotter and unpack it in its own folder
        JS8Spotter runs in-place, which means that it may be executed directly after extraction,
        without any installation or moving of files. It also means you may have multiple versions
        on one computer and run the one you want. When upgrading, you'll want to get the latest
        version, unpack it, and get it operational before you replace your previous version files
        and shortcuts.

Step 3: Copy your backup database into the new version folder
        Take a copy of the backup js8spotter.db file that you copied in Step 1 and place it in your
        new latest version JS8Spotter folder, overwriting the empty one that is in that folder. The
        file name is always "js8spotter.db", so if you've renamed it for the backup process make
        sure to change it back.

Step 4: Run the dbtool in the new version folder
        Once you have your database file in place, run the dbtool to upgrade your file. It will
        report your current file version and it will examine your database for missing structure.
        Once you've examined the file, you can click one button to execute the upgrade. The program
        will report if the upgrade was a success. Close and re-open the dbtool and run it again
        to verify that your database now reports the correct version.

Step 5: (Optional) Copy your custom forms and notification WAVs
        If you have custom forms or custom notification sounds, you will want to copy them from your
        old folder into the new folder. Please review the changelog and website to see if any
        modifications have been made to the MCForms format in the latest version.

At this point your database file is upgraded and may be used with the latest version. You may wish
to move/replace your old version files with the new files. It is recommended you simply rename the
old folder, and replace it with the new. You may need to update your shortcuts, if any, and
launchers.

73, Joe KF7MIX
