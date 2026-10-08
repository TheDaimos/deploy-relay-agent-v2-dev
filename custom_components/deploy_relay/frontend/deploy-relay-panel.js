import "./deploy-relay-diagnostics.js?v=1.0.0";

const TEXT = {
  de: {
    subtitle: "Sicheres Deployment für Git-Projekte",
    locked: "GESPERRT",
    development: "ENTWICKLUNG",
    unlock: "3 · Schreibzugriff freigeben",
    unlockLoading: "Schreibzugriff wird geprüft und aktiviert …",
    lock: "Schreibzugriff wieder sperren",
    lockLoading: "Schreibzugriff wird gesperrt …",
    modeWorking: "DRA prüft und übernimmt den angeforderten Schreibzugriffsstatus. Bitte warten …",
    unlockConfirm: "Schreibzugriff für die Installation freigeben? Danach sind ausdrücklich bestätigte Deployment-Schreibzugriffe möglich. Nach jedem Home-Assistant-Neustart ist Deploy Relay wieder GESPERRT.",
    workflowTitle: "Geführter Ablauf",
    workflowHint: "Die Schritte sind nummeriert. Antippen springt zum passenden Bereich; Schritt 2 startet die Vorschau direkt.",
    workflowStep1: "Stand auswählen",
    workflowStep2: "Vorschau prüfen",
    workflowStep3: "Schreibzugriff",
    workflowStep4: "Installieren",
    nextProject: "Als Nächstes: Projekt auswählen.",
    nextSource: "Als Nächstes: empfohlenen Stand auswählen.",
    nextPreview: "Als Nächstes: Vorschau berechnen und Änderungen prüfen.",
    nextUnlock: "Als Nächstes: Schreibzugriff für die Installation freigeben.",
    nextInstall: "Als Nächstes: geprüfte Änderungen installieren.",
    nextRestart: "Als Nächstes: Home Assistant vollständig neu starten.",
    nextFrontendReload: "Als Nächstes: Frontend / Companion App neu laden.",
    nextDone: "Installation abgeschlossen.",
    noChangesNext: "Keine Installation nötig: Quelle und lokaler Stand sind identisch.",
    projects: "Projekte",
    refresh: "Aktualisieren",
    importProject: "Projekt hinzufügen",
    importTitle: "Neues Projekt hinzufügen",
    removeProject: "Projekt entfernen",
    removeTitle: "Projekt entfernen",
    removeWarning: "Entfernt nur die DRA-Projektkonfiguration einschließlich gespeicherter Zugangsdaten und Quellauswahl. Bereits installierte Projektdateien werden nicht gelöscht.",
    removeTypePrompt: "Zur Bestätigung den Projektnamen exakt eingeben:",
    removeConfirm: "Projekt endgültig entfernen",
    removeDone: "Projekt wurde aus DRA entfernt.",
    backups: "Sicherungen",
    backupTitle: "Sicherungen & Wiederherstellung",
    backupIntro: "DRA sichert vor jedem Deployment den betroffenen alten Dateistand. Standardmäßig bleiben pro Projekt die letzten 10 Sicherungen erhalten.",
    backupRetention: "Aufbewahrte Sicherungen",
    backupRetentionHint: "Projektbezogen einstellbar. Mindestens 3 Sicherungen bleiben als Sicherheitsbasis erhalten.",
    backupRetentionSave: "Aufbewahrung speichern",
    backupRetentionConfirm: "Aufbewahrung für dieses Projekt ändern? Beim Reduzieren entfernt DRA die ältesten verifizierten Sicherungen dauerhaft.",
    backupRetentionSaved: "Aufbewahrung gespeichert.",
    backupRetentionCleanupWarning: "Hinweis: ältere Sicherungen konnten nicht vollständig bereinigt werden.",
    backupSavedVersion: "Gesicherter Stand",
    backupTargetVersion: "Deployment-Ziel",
    backupEmpty: "Für dieses Projekt sind noch keine Sicherungen vorhanden.",
    backupFiles: "Dateien",
    backupStored: "Gesichert",
    backupRestore: "Wiederherstellen",
    backupRestoreConfirm: "Diese Sicherung wiederherstellen? DRA legt zuerst eine neue Sicherheitssicherung des aktuellen Zustands an, stellt dann die gewählte Sicherung wieder her und prüft anschließend die SHA-256-Werte.",
    backupRestoreNeedsDevelopment: "Für die Wiederherstellung zuerst den Schreibzugriff (ENTWICKLUNG) freigeben.",
    backupRestoreRunning: "Wiederherstellung läuft …",
    backupRestoreDone: "Sicherung erfolgreich wiederhergestellt.",
    backupRestoreSafety: "Sicherheitssicherung vor Wiederherstellung",
    backupKindDeployment: "Vor Deployment",
    backupKindRestoreSafety: "Vor Wiederherstellung",
    backupLegacy: "Älterer Transaktions-Rollbackpunkt · nicht direkt wiederherstellbar",
    backupClose: "Schließen",
    batchUpdate: "Sammelupdate",
    batchTitle: "Sammelaktualisierung",
    batchIntro: "Mehrere Projekte gegen ihren empfohlenen Stand prüfen und nacheinander installieren. DRA ermittelt anschließend automatisch, ob Frontend-Neuladen oder ein Home-Assistant-Neustart erforderlich ist.",
    batchSelfLast: "Deploy Relay wird bei einer Sammelinstallation automatisch zuletzt installiert.",
    batchPendingRestart: "Ein Neustart steht bereits aus. Andere Projekte können trotzdem weiter geprüft und installiert werden.",
    batchCheck: "Ausgewählte prüfen",
    batchCheckRunning: "Prüfe ausgewählte Projekte …",
    batchCheckDone: "✓ Prüfung abgeschlossen",
    batchUnlock: "Schreibzugriff freigeben",
    batchUnlockDone: "✓ Schreibzugriff freigegeben",
    batchUnlockRunning: "Schreibzugriff wird aktiviert …",
    batchInstall: "Projekte installieren",
    batchInstallRunning: "Installiere {current}/{total} · {project} …",
    batchInstallDone: "✓ Installation abgeschlossen",
    batchClose: "Schließen",
    batchInstallConfirm: "{count} Projekte nacheinander installieren? Deploy Relay wird – falls ausgewählt – zuletzt installiert. DRA ermittelt danach die tatsächlich notwendige Nachaktion.",
    batchUnlockConfirm: "Schreibzugriff für die Sammelinstallation freigeben?",
    batchNoSelection: "Mindestens ein Projekt auswählen.",
    batchNoUpdates: "Keine ausgewählten Projekte benötigen eine Installation.",
    batchBlocked: "Mindestens ein ausgewähltes Projekt ist blockiert. Vor der Sammelinstallation zuerst den Blocker beheben.",
    batchReady: "Bereit",
    batchCurrent: "Aktuell",
    batchChecking: "Prüfe …",
    batchPending: "Noch nicht geprüft",
    batchInstalling: "Installiere …",
    batchInstalled: "Installiert",
    batchInstalledRestart: "Installiert · Neustart erforderlich",
    batchInstalledFrontend: "Installiert · Frontend neu laden",
    batchError: "Fehler",
    batchBlocker: "Blockiert",
    batchRestartSummary: "Installationen abgeschlossen. Home Assistant kann jetzt einmal vollständig neu gestartet werden.",
    batchFrontendSummary: "Installationen abgeschlossen. Frontend / Companion App neu laden genügt; kein Home-Assistant-Neustart erforderlich.",
    batchDoneSummary: "Installationen abgeschlossen. Keine weitere Nachaktion erforderlich.",
    batchPartial: "Sammelinstallation wurde nach einem Fehler gestoppt. Bereits abgeschlossene Projekte bleiben installiert.",
    repository: "GitHub-Repository",
    manifestPath: "Manifestpfad",
    githubToken: "GitHub-Lesetoken",
    tokenHint: "Für private Repositories. Der Token wird nach dem Speichern nicht wieder angezeigt.",
    cancel: "Abbrechen",
    importNow: "Projekt importieren",
    selectProject: "Projekt auswählen",
    repo: "Repository",
    manifest: "Manifest",
    token: "GitHub-Zugang",
    tokenOk: "Lesetoken vorhanden",
    tokenMissing: "Kein Token",
    source: "Quelle & Version",
    chooseSource: "Quelle auswählen",
    manualCommit: "Commit-SHA manuell",
    applySource: "Quelle übernehmen",
    sourceSelectionPending: "Auswahl noch nicht übernommen · bitte Quelle übernehmen",
    sourceRefAdvanced: "Der ausgewählte Branch zeigt inzwischen auf einen neuen Commit · bitte Quelle erneut übernehmen",
    preview: "Vorschau",
    loadPreview: "2 · Vorschau berechnen",
    reloadPreview: "2 · Vorschau neu berechnen",
    previewLoading: "Vorschau wird berechnet …",
    previewReady: "✓ 2 · Vorschau berechnet",
    previewReadyHint: "Vorschau erfolgreich berechnet. Änderungen und Warnungen unten prüfen.",
    checksumValid: "SHA-256-Prüfsummen geprüft",
    checksumValidDetail: "Prüfsummen vollständig berechnet und Vergleich abgeschlossen.",
    restartPendingTop: "Neustart",
    search: "Dateien durchsuchen …",
    all: "Alle",
    add: "Neu",
    change: "Geändert",
    remove: "Entfernen",
    removed: "Entfernt",
    unchanged: "Unverändert",
    operation: "Aktion",
    path: "Zielpfad",
    size: "Größe",
    sourceHash: "Git SHA-256",
    targetHash: "Lokal SHA-256",
    noProjects: "Noch kein Projekt importiert.",
    noSource: "Noch keine Quelle ausgewählt.",
    noPreview: "Noch keine Vorschau berechnet.",
    loading: "Lade …",
    project: "Projekt",
    progressApprox: "Fortschritt",
    progressInitialProjects: "Projektliste wird geladen …",
    progressInitialSources: "Projektquellen werden vorbereitet …",
    progressInitialReady: "Oberfläche wird freigegeben …",
    progressRefresh: "DRA-Daten werden aktualisiert …",
    progressSources: "Projektquellen werden geladen …",
    progressPreviewStart: "Vorschau wird vorbereitet …",
    progressPreviewInventory: "Quelldateien werden erfasst …",
    progressPreviewCompare: "Lokale Dateien und Prüfsummen werden verglichen …",
    progressPreviewFinalize: "Vorschau wird aufbereitet …",
    progressInstallStart: "Installation wird vorbereitet …",
    progressInstallStaging: "Staging und Integritätsprüfung laufen …",
    progressInstallBackup: "Sicherung und Installation laufen …",
    progressInstallVerify: "Installierter Stand wird verifiziert …",
    progressRestoreStart: "Wiederherstellung wird vorbereitet …",
    progressRestoreSafety: "Sicherheitssicherung wird erstellt …",
    progressRestoreApply: "Dateien werden wiederhergestellt …",
    progressRestoreVerify: "Wiederherstellung wird verifiziert …",
    progressMode: "Schreibzugriffsstatus wird übernommen …",
    progressBatchCheck: "Sammelprüfung läuft …",
    progressBatchInstall: "Sammelinstallation läuft …",
    readOnly: "Gesperrter Betrieb",
    writesOff: "Deployment-Schreibzugriffe sind deaktiviert. Vorschau und Diagnose bleiben verfügbar.",
    developmentMode: "Entwicklungsmodus aktiv",
    writesOn: "Schreibzugriffe sind nur für ausdrücklich bestätigte Installationen freigegeben. Nach einem Neustart ist Deploy Relay wieder gesperrt.",
    install: "4 · Änderungen installieren",
    installOne: "1 Änderung installieren",
    installMany: "{count} Änderungen installieren",
    installLoading: "Installation läuft …",
    installWorking: "DRA arbeitet. Staging, Sicherung, Installation und Integritätsprüfung laufen.",
    installConfirm: "Die angezeigte Quelle wird jetzt erneut geprüft, vollständig in Staging geladen, gesichert und anschließend installiert. Fortfahren?",
    installDone: "Installation erfolgreich",
    transaction: "Transaktion",
    backup: "Sicherung",
    restartRequired: "Home Assistant muss jetzt vollständig neu gestartet werden.",
    restartRequiredTitle: "NEUSTART ERFORDERLICH",
    restartPendingShort: "Neustart erforderlich",
    restartRequiredBody: "Die Installation ist abgeschlossen, aber der neue Projektstand ist erst nach einem vollständigen Home-Assistant-Neustart aktiv.",
    restartRequiredAction: "Home Assistant jetzt vollständig neu starten. Danach Deploy Relay erneut öffnen.",
    restartRequiredDialog: "Installation erfolgreich.\n\nHome Assistant muss jetzt vollständig neu gestartet werden, damit der neue Stand aktiv wird.",
    noRestartRequired: "Kein vollständiger Home-Assistant-Neustart erforderlich.",
    frontendReloadRequired: "Frontend / Companion App neu laden; kein Home-Assistant-Neustart erforderlich.",
    frontendReloadTitle: "FRONTEND NEU LADEN",
    frontendReloadBody: "Die Installation enthält ausschließlich eindeutig erkannte Frontend-Dateien. Ein vollständiger Home-Assistant-Neustart ist nicht erforderlich.",
    frontendReloadAction: "Frontend jetzt neu laden",
    lifecycleTitle: "Nach Installation",
    lifecycleFrontend: "Frontend / Companion App neu laden",
    lifecycleRestart: "Home Assistant vollständig neu starten",
    lifecycleNone: "Keine Nachaktion erforderlich",
    lifecycleCompactFrontend: "↻ Frontend-Neuladen genügt",
    lifecycleCompactRestart: "⚠ HA-Neustart erforderlich",
    lifecycleCompactNone: "✓ Keine Nachaktion erforderlich",
    versionCheck: "Versions- und Regressionsprüfung",
    gitVersion: "Git-Quelle",
    localVersion: "Lokal",
    versionMarker: "Erkannt über",
    regressionWarning: "REGRESSIONSWARNUNG: Die gewählte Git-Version ist älter als der lokal installierte Stand.",
    versionRegression: "Lokaler/Teststand ist neuer als der empfohlene DEV-Stand.",
    sameVersionWarning: "Warnung: Die Versionskennung ist gleich, aber verwaltete Dateien unterscheiden sich. Änderungen vor Installation prüfen.",
    unknownVersionWarning: "Warnung: Keine gemeinsame Versionskennung erkannt; die Vorschau enthält Löschungen.",
    upgradeDetected: "Upgrade erkannt.",
    sameVersionDetected: "Versionsstand identisch.",
    versionUnknown: "Versionsreihenfolge nicht eindeutig bestimmbar.",
    regressionConfirm: "ACHTUNG: Damit wird bewusst eine ältere Git-Version über einen neueren lokalen Stand installiert. Dies kann Funktionen und Dateien zurücksetzen. Regression ausdrücklich durchführen?",
    branch: "Branch",
    tag: "Tag",
    release: "Release",
    commit: "Commit",
    config: "Projekt / Token verwalten",
    truncated: "Die Quellenliste wurde begrenzt.",
    files: "Dateien",
    recommendedDeployment: "Empfohlenes Deployment",
    recommendedCurrent: "Empfohlener aktueller Stand",
    recommendedAvailable: "Empfohlener Stand verfügbar",
    recommendedNewer: "Neuerer empfohlener Stand verfügbar",
    recommendedDifferent: "Ausgewählter Stand weicht von der Empfehlung ab",
    recommendedFallback: "Keine explizite Deployment-Kanaldatei; nur Default-Branch-Fallback",
    recommendedUnavailable: "Empfohlenes Deployment konnte nicht sicher bestimmt werden.",
    channel: "Kanal",
    useRecommended: "1 · Empfohlenen Stand auswählen",
    advancedSources: "Erweiterte Quellenauswahl",
    advancedWarning: "Nur verwenden, wenn du bewusst von der empfohlenen Deployment-Quelle abweichen willst.",
    unrecommendedConfirm: "ACHTUNG: Der ausgewählte Stand ist nicht das aktuell empfohlene Deployment. Nur fortfahren, wenn du bewusst einen anderen oder älteren Stand installieren willst.",
    recommendationPolicy: "Deployment-Kanal",
  },
  en: {
    subtitle: "Safe deployment for Git-managed projects",
    locked: "LOCKED",
    development: "DEVELOPMENT",
    unlock: "3 · Enable write access",
    unlockLoading: "Checking and enabling write access …",
    lock: "Lock write access again",
    lockLoading: "Locking write access …",
    modeWorking: "DRA is checking and applying the requested write-access state. Please wait …",
    unlockConfirm: "Enable write access for installation? Explicitly confirmed deployment writes will then be allowed. Deploy Relay returns to LOCKED after every Home Assistant restart.",
    workflowTitle: "Guided flow",
    workflowHint: "Steps are numbered. Tap to jump to the matching area; step 2 starts the preview directly.",
    workflowStep1: "Select build",
    workflowStep2: "Review preview",
    workflowStep3: "Write access",
    workflowStep4: "Install",
    nextProject: "Next: select a project.",
    nextSource: "Next: select the recommended build.",
    nextPreview: "Next: build the preview and review the changes.",
    nextUnlock: "Next: enable write access for the installation.",
    nextInstall: "Next: install the reviewed changes.",
    nextRestart: "Next: fully restart Home Assistant.",
    nextFrontendReload: "Next: reload the frontend / Companion App.",
    nextDone: "Installation completed.",
    noChangesNext: "No installation needed: source and local state are identical.",
    projects: "Projects",
    refresh: "Refresh",
    importProject: "Add project",
    importTitle: "Add new project",
    removeProject: "Remove project",
    removeTitle: "Remove project",
    removeWarning: "Removes only the DRA project configuration including stored credentials and source selection. Already deployed project files are not deleted.",
    removeTypePrompt: "To confirm, type the project name exactly:",
    removeConfirm: "Remove project permanently",
    removeDone: "Project was removed from DRA.",
    backups: "Backups",
    backupTitle: "Backups & restore",
    backupIntro: "DRA backs up the affected previous file state before every deployment. By default, the latest 10 backups are retained per project.",
    backupRetention: "Retained backups",
    backupRetentionHint: "Configured per project. At least 3 backups remain as the safety baseline.",
    backupRetentionSave: "Save retention",
    backupRetentionConfirm: "Change retention for this project? Lowering the value permanently removes the oldest verified backups.",
    backupRetentionSaved: "Retention saved.",
    backupRetentionCleanupWarning: "Note: older backups could not be pruned completely.",
    backupSavedVersion: "Saved build",
    backupTargetVersion: "Deployment target",
    backupEmpty: "No backups exist for this project yet.",
    backupFiles: "Files",
    backupStored: "Stored",
    backupRestore: "Restore",
    backupRestoreConfirm: "Restore this backup? DRA first creates a new safety backup of the current state, then restores the selected backup and verifies the SHA-256 values.",
    backupRestoreNeedsDevelopment: "Enable write access (DEVELOPMENT) before restoring a backup.",
    backupRestoreRunning: "Restore in progress …",
    backupRestoreDone: "Backup restored successfully.",
    backupRestoreSafety: "Safety backup before restore",
    backupKindDeployment: "Before deployment",
    backupKindRestoreSafety: "Before restore",
    backupLegacy: "Legacy transaction rollback point · not directly restorable",
    backupClose: "Close",
    batchUpdate: "Batch update",
    batchTitle: "Batch update",
    batchIntro: "Check multiple projects against their recommended builds and install them sequentially. DRA then determines whether a frontend reload or a Home Assistant restart is actually required.",
    batchSelfLast: "Deploy Relay is installed last automatically in a batch.",
    batchPendingRestart: "A restart is already pending. Other projects can still be checked and installed.",
    batchCheck: "Check selected",
    batchCheckRunning: "Checking selected projects …",
    batchCheckDone: "✓ Check completed",
    batchUnlock: "Enable write access",
    batchUnlockDone: "✓ Write access enabled",
    batchUnlockRunning: "Enabling write access …",
    batchInstall: "Install projects",
    batchInstallRunning: "Installing {current}/{total} · {project} …",
    batchInstallDone: "✓ Installation completed",
    batchClose: "Close",
    batchInstallConfirm: "Install {count} projects sequentially? Deploy Relay will be installed last when selected. DRA will determine the required post-install action afterwards.",
    batchUnlockConfirm: "Enable write access for the batch installation?",
    batchNoSelection: "Select at least one project.",
    batchNoUpdates: "None of the selected projects needs installation.",
    batchBlocked: "At least one selected project is blocked. Resolve the blocker before batch installation.",
    batchReady: "Ready",
    batchCurrent: "Current",
    batchChecking: "Checking …",
    batchPending: "Not checked yet",
    batchInstalling: "Installing …",
    batchInstalled: "Installed",
    batchInstalledRestart: "Installed · restart required",
    batchInstalledFrontend: "Installed · reload frontend",
    batchError: "Error",
    batchBlocker: "Blocked",
    batchRestartSummary: "Installations completed. Home Assistant can now be restarted once.",
    batchFrontendSummary: "Installations completed. Reloading the frontend / Companion App is sufficient; no Home Assistant restart is required.",
    batchDoneSummary: "Installations completed. No further post-install action is required.",
    batchPartial: "Batch installation stopped after an error. Projects already completed remain installed.",
    repository: "GitHub repository",
    manifestPath: "Manifest path",
    githubToken: "GitHub read token",
    tokenHint: "For private repositories. The token is not shown again after it is stored.",
    cancel: "Cancel",
    importNow: "Import project",
    selectProject: "Select project",
    repo: "Repository",
    manifest: "Manifest",
    token: "GitHub access",
    tokenOk: "Read token configured",
    tokenMissing: "No token",
    source: "Source & version",
    chooseSource: "Select source",
    manualCommit: "Manual commit SHA",
    applySource: "Use source",
    sourceSelectionPending: "Selection not applied yet · use source to confirm",
    sourceRefAdvanced: "The selected branch now points to a newer commit · apply the source again",
    preview: "Preview",
    loadPreview: "2 · Build preview",
    reloadPreview: "2 · Rebuild preview",
    previewLoading: "Building preview …",
    previewReady: "✓ 2 · Preview calculated",
    previewReadyHint: "Preview calculated successfully. Review changes and warnings below.",
    checksumValid: "SHA-256 checksums verified",
    checksumValidDetail: "Checksums calculated completely and comparison finished.",
    restartPendingTop: "Restart",
    search: "Search files …",
    all: "All",
    add: "Add",
    change: "Changed",
    remove: "Remove",
    removed: "Removed",
    unchanged: "Unchanged",
    operation: "Action",
    path: "Target path",
    size: "Size",
    sourceHash: "Git SHA-256",
    targetHash: "Local SHA-256",
    noProjects: "No project imported yet.",
    noSource: "No source selected yet.",
    noPreview: "No preview calculated yet.",
    loading: "Loading …",
    project: "Project",
    progressApprox: "Progress",
    progressInitialProjects: "Loading project list …",
    progressInitialSources: "Preparing project sources …",
    progressInitialReady: "Enabling interface …",
    progressRefresh: "Refreshing DRA data …",
    progressSources: "Loading project sources …",
    progressPreviewStart: "Preparing preview …",
    progressPreviewInventory: "Inventorying source files …",
    progressPreviewCompare: "Comparing local files and checksums …",
    progressPreviewFinalize: "Finalizing preview …",
    progressInstallStart: "Preparing installation …",
    progressInstallStaging: "Staging and integrity checks in progress …",
    progressInstallBackup: "Backup and installation in progress …",
    progressInstallVerify: "Verifying installed state …",
    progressRestoreStart: "Preparing restore …",
    progressRestoreSafety: "Creating safety backup …",
    progressRestoreApply: "Restoring files …",
    progressRestoreVerify: "Verifying restored state …",
    progressMode: "Applying write-access state …",
    progressBatchCheck: "Batch check in progress …",
    progressBatchInstall: "Batch installation in progress …",
    readOnly: "Locked mode",
    writesOff: "Deployment writes are disabled. Preview and diagnostics remain available.",
    developmentMode: "Development mode active",
    writesOn: "Writes are enabled only for explicitly confirmed installs. Deploy Relay returns to LOCKED after restart.",
    install: "4 · Install changes",
    installOne: "Install 1 change",
    installMany: "Install {count} changes",
    installLoading: "Installation in progress …",
    installWorking: "DRA is working. Staging, backup, installation and integrity verification are running.",
    installConfirm: "The selected source will be checked again, fully staged, backed up and then installed. Continue?",
    installDone: "Installation successful",
    transaction: "Transaction",
    backup: "Backup",
    restartRequired: "Home Assistant now requires a full restart.",
    restartRequiredTitle: "RESTART REQUIRED",
    restartPendingShort: "Restart required",
    restartRequiredBody: "The installation is complete, but the new project build becomes active only after a full Home Assistant restart.",
    restartRequiredAction: "Restart Home Assistant fully now. Then reopen Deploy Relay.",
    restartRequiredDialog: "Installation successful.\n\nHome Assistant must now be fully restarted before the new build is active.",
    noRestartRequired: "No full Home Assistant restart is required.",
    frontendReloadRequired: "Reload the frontend / Companion App; no Home Assistant restart is required.",
    frontendReloadTitle: "RELOAD FRONTEND",
    frontendReloadBody: "The installation contains only unambiguously classified frontend files. A full Home Assistant restart is not required.",
    frontendReloadAction: "Reload frontend now",
    lifecycleTitle: "After installation",
    lifecycleFrontend: "Reload frontend / Companion App",
    lifecycleRestart: "Fully restart Home Assistant",
    lifecycleNone: "No post-install action required",
    lifecycleCompactFrontend: "↻ Frontend reload is sufficient",
    lifecycleCompactRestart: "⚠ HA restart required",
    lifecycleCompactNone: "✓ No post-install action required",
    versionCheck: "Version and regression check",
    gitVersion: "Git source",
    localVersion: "Local",
    versionMarker: "Detected via",
    regressionWarning: "REGRESSION WARNING: The selected Git version is older than the locally installed build.",
    versionRegression: "Local/test build is newer than the recommended DEV build.",
    sameVersionWarning: "Warning: The version marker is unchanged, but managed files differ. Review changes before installation.",
    unknownVersionWarning: "Warning: No common version marker was detected and the preview contains removals.",
    upgradeDetected: "Upgrade detected.",
    sameVersionDetected: "Version is identical.",
    versionUnknown: "Version order cannot be determined reliably.",
    regressionConfirm: "WARNING: This will deliberately install an older Git version over a newer local build. Features and files may be reverted. Explicitly perform this regression?",
    branch: "Branch",
    tag: "Tag",
    release: "Release",
    commit: "Commit",
    config: "Manage project / token",
    truncated: "The source list was limited.",
    files: "Files",
    recommendedDeployment: "Recommended deployment",
    recommendedCurrent: "Current recommended build",
    recommendedAvailable: "Recommended build available",
    recommendedNewer: "Newer recommended build available",
    recommendedDifferent: "Selected source differs from the recommendation",
    recommendedFallback: "No explicit deployment channel policy; default-branch fallback only",
    recommendedUnavailable: "Recommended deployment could not be verified safely.",
    channel: "Channel",
    useRecommended: "1 · Select recommended build",
    advancedSources: "Advanced source selection",
    advancedWarning: "Use only when you intentionally want to deviate from the recommended deployment source.",
    unrecommendedConfirm: "WARNING: The selected build is not the current recommended deployment. Continue only if you intentionally want to install another or older build.",
    recommendationPolicy: "Deployment channel",
  },
};

const esc = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const shortSha = (value) => (value ? String(value).slice(0, 12) : "—");

const formatBytes = (value) => {
  if (value == null) return "—";
  const bytes = Number(value);
  if (!Number.isFinite(bytes)) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MiB`;
};

class DeployRelayPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._state = null;
    this._selectedProjectId = null;
    this._sources = null;
    this._preview = null;
    this._installResult = null;
    this._filter = "all";
    this._search = "";
    this._loading = false;
    this._previewLoading = false;
    this._modeLoading = false;
    this._installLoading = false;
    this._error = "";
    this._sourceChoice = "";
    this._manualCommit = "";
    this._advancedSourcesOpen = false;
    this._showImport = false;
    this._showRemove = false;
    this._showBatch = false;
    this._showBackups = false;
    this._backups = [];
    this._backupRetention = 10;
    this._backupLimits = { minimum: 3, maximum: 100 };
    this._backupLoading = false;
    this._restoreLoading = false;
    this._backupMessage = "";
    this._restoreResult = null;
    this._batchSelected = new Set();
    this._batchItems = {};
    this._batchRunning = false;
    this._batchPhase = "idle";
    this._batchCheckComplete = false;
    this._batchInstallComplete = false;
    this._batchInstallFailed = false;
    this._batchProgress = { current: 0, total: 0, project: "" };
    this._batchMessage = "";
    this._removeConfirmText = "";
    this._importRepo = "";
    this._importManifest = "deploy-relay.json";
    this._importToken = "";
    this._started = false;
    this._initializing = true;
    this._progress = null;
    this._progressTimer = null;
  }

  set hass(value) {
    this._hass = value;
    if (!this._started && value) {
      this._started = true;
      this._loadState();
    }
  }

  get hass() {
    return this._hass;
  }

  set panel(value) {
    this._panel = value;
  }

  set narrow(value) {
    this._narrow = value;
  }

  set route(value) {
    this._route = value;
  }

  _t(key) {
    const lang = this.hass?.language?.toLowerCase?.().startsWith("de") ? "de" : "en";
    return TEXT[lang][key] ?? key;
  }

  async _call(message) {
    if (!this.hass) throw new Error("Home Assistant connection unavailable");
    return this.hass.callWS(message);
  }

  _clearProgressTimer() {
    if (this._progressTimer) {
      window.clearInterval(this._progressTimer);
      this._progressTimer = null;
    }
  }

  _progressLabel(kind, percent) {
    if (kind === "initial") {
      if (percent < 45) return this._t("progressInitialProjects");
      if (percent < 88) return this._t("progressInitialSources");
      return this._t("progressInitialReady");
    }
    if (kind === "refresh") return this._t("progressRefresh");
    if (kind === "sources") return this._t("progressSources");
    if (kind === "mode") return this._t("progressMode");
    if (kind === "preview") {
      if (percent < 24) return this._t("progressPreviewStart");
      if (percent < 50) return this._t("progressPreviewInventory");
      if (percent < 82) return this._t("progressPreviewCompare");
      return this._t("progressPreviewFinalize");
    }
    if (kind === "install") {
      if (percent < 22) return this._t("progressInstallStart");
      if (percent < 48) return this._t("progressInstallStaging");
      if (percent < 80) return this._t("progressInstallBackup");
      return this._t("progressInstallVerify");
    }
    if (kind === "restore") {
      if (percent < 24) return this._t("progressRestoreStart");
      if (percent < 50) return this._t("progressRestoreSafety");
      if (percent < 80) return this._t("progressRestoreApply");
      return this._t("progressRestoreVerify");
    }
    if (kind === "batch_check") return this._t("progressBatchCheck");
    if (kind === "batch_install") return this._t("progressBatchInstall");
    return this._t("loading");
  }

  _startProgress(kind, detail = "", { start = 4, cap = 92, exact = false } = {}) {
    this._clearProgressTimer();
    this._progress = { kind, percent: start, detail, cap, exact };
    this._progressTimer = window.setInterval(() => {
      if (!this._progress || this._progress.kind !== kind) return;
      const current = Number(this._progress.percent || 0);
      const increment = current < 45 ? 4 : current < 72 ? 2 : 1;
      this._progress.percent = Math.min(Number(this._progress.cap || cap), current + increment);
      this._render();
    }, 850);
    this._render();
  }

  _setProgress(percent, detail = null, { exact = null } = {}) {
    if (!this._progress) return;
    this._progress.percent = Math.max(0, Math.min(100, Math.round(Number(percent) || 0)));
    if (detail !== null) this._progress.detail = detail;
    if (exact !== null) this._progress.exact = Boolean(exact);
    this._render();
  }

  _finishProgress() {
    if (!this._progress) return;
    this._clearProgressTimer();
    this._progress.percent = 100;
    this._progress.cap = 100;
    this._render();
    const kind = this._progress.kind;
    window.setTimeout(() => {
      if (this._progress?.kind === kind && Number(this._progress.percent) === 100) {
        this._progress = null;
        this._render();
      }
    }, 650);
  }

  _cancelProgress() {
    this._clearProgressTimer();
    this._progress = null;
    this._render();
  }

  _progressMarkup() {
    if (!this._progress) return "";
    const percent = Math.max(0, Math.min(100, Math.round(Number(this._progress.percent) || 0)));
    const label = this._progressLabel(this._progress.kind, percent);
    const prefix = this._progress.exact ? "" : "≈ ";
    return `
      <div class="operation-progress" role="status" aria-live="polite">
        <div class="operation-progress-head">
          <strong>${esc(label)}</strong>
          <span>${esc(this._t("progressApprox"))}: ${prefix}${percent} %</span>
        </div>
        <div class="operation-progress-track" role="progressbar"
             aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}">
          <div class="operation-progress-fill" style="width:${percent}%"></div>
        </div>
        ${this._progress.detail ? `<small>${esc(this._progress.detail)}</small>` : ""}
      </div>
    `;
  }

  async _loadState({ keepProject = true } = {}) {
    const initial = this._initializing;
    this._startProgress(initial ? "initial" : "refresh", "", { start: 5, cap: 92 });
    this._setLoading(true);
    let failed = false;
    try {
      const state = await this._call({ type: "deploy_relay/panel/state" });
      this._state = state;
      this._setProgress(initial ? 42 : 48, `${state.projects.length} ${this._t("projects")}`);
      const exists = state.projects.some(
        (project) => project.subentry_id === this._selectedProjectId
      );
      if (!keepProject || !exists) {
        this._selectedProjectId = state.projects[0]?.subentry_id ?? null;
      }
      this._error = "";
      if (this._selectedProjectId) {
        this._setProgress(initial ? 58 : 62);
        await this._loadSources({ nested: true });
        this._setProgress(94);
      }
    } catch (err) {
      failed = true;
      this._error = err?.message || String(err);
    } finally {
      if (initial) this._initializing = false;
      this._setLoading(false);
      if (failed) this._cancelProgress();
      else this._finishProgress();
      this._render();
    }
  }

  async _loadSources({ nested = false } = {}) {
    if (!this._selectedProjectId) return;
    if (!nested) {
      this._startProgress("sources", this._project()?.title || "", { start: 8, cap: 92 });
      this._setLoading(true);
    }
    let failed = false;
    try {
      this._sources = await this._call({
        type: "deploy_relay/panel/sources",
        subentry_id: this._selectedProjectId,
      });
      const project = this._project();
      if (project?.selected_source_kind && project?.selected_source_ref) {
        this._sourceChoice = JSON.stringify({
          kind: project.selected_source_kind,
          ref: project.selected_source_ref,
        });
      } else if (this._sources?.recommended?.available) {
        this._sourceChoice = JSON.stringify({
          kind: this._sources.recommended.kind,
          ref: this._sources.recommended.ref,
        });
      } else {
        const first = this._sources.candidates[0];
        this._sourceChoice = first
          ? JSON.stringify({ kind: first.kind, ref: first.ref })
          : "";
      }
      if (!nested) this._setProgress(94, `${this._sources.candidates?.length || 0} Quellen`);
      this._error = "";
    } catch (err) {
      failed = true;
      this._sources = null;
      this._error = err?.message || String(err);
      if (nested) throw err;
    } finally {
      if (!nested) {
        this._setLoading(false);
        if (failed) this._cancelProgress();
        else this._finishProgress();
        this._render();
      }
    }
  }

  _sourceChoiceCandidate() {
    if (!this._sourceChoice || this._sourceChoice === "__manual__") return null;
    let decoded;
    try {
      decoded = JSON.parse(this._sourceChoice);
    } catch (_error) {
      return null;
    }
    return (this._sources?.candidates || []).find(
      (item) => item.kind === decoded.kind && item.ref === decoded.ref
    ) || null;
  }

  _sourceMovingRefAdvanced() {
    const project = this._project();
    const candidate = this._sourceChoiceCandidate();
    if (
      !project?.selected_source_kind ||
      !project?.selected_source_ref ||
      !project?.selected_source_commit ||
      !candidate?.commit_sha
    ) return false;

    let decoded;
    try {
      decoded = JSON.parse(this._sourceChoice);
    } catch (_error) {
      return false;
    }

    return (
      decoded.kind === project.selected_source_kind &&
      decoded.ref === project.selected_source_ref &&
      candidate.commit_sha !== project.selected_source_commit
    );
  }

  _sourceSelectionIsPending() {
    const project = this._project();
    const appliedSourceChoice = (
      project?.selected_source_kind && project?.selected_source_ref
    )
      ? JSON.stringify({
          kind: project.selected_source_kind,
          ref: project.selected_source_ref,
        })
      : "";

    return Boolean(
      this._sourceChoice &&
      this._sourceChoice !== "__manual__" &&
      (
        this._sourceChoice !== appliedSourceChoice ||
        this._sourceMovingRefAdvanced()
      )
    ) || Boolean(
      this._sourceChoice === "__manual__" &&
      this._manualCommit.trim()
    );
  }

  _syncAdvancedSourceControls() {
    const details = this.shadowRoot?.querySelector("#advanced-sources");
    if (details) {
      details.open = true;
      this._advancedSourcesOpen = true;
    }

    const manualRow = this.shadowRoot?.querySelector("#manual-row");
    if (manualRow) {
      manualRow.style.display = this._sourceChoice === "__manual__" ? "" : "none";
    }

    const pending = this._sourceSelectionIsPending();
    const apply = this.shadowRoot?.querySelector("#apply-source");
    if (apply) {
      apply.classList.toggle("primary", pending);
    }

    const notice = this.shadowRoot?.querySelector(".source-selection-pending");
    if (notice) {
      notice.style.display = pending ? "" : "none";
      notice.textContent = this._sourceMovingRefAdvanced()
        ? this._t("sourceRefAdvanced")
        : this._t("sourceSelectionPending");
    }
  }

  async _selectSource() {
    if (!this._selectedProjectId) return;
    let kind;
    let ref;

    if (this._sourceChoice === "__manual__") {
      kind = "commit";
      ref = this._manualCommit.trim();
      if (!ref) return;
    } else {
      const decoded = JSON.parse(this._sourceChoice);
      kind = decoded.kind;
      ref = decoded.ref;
    }

    this._setLoading(true);
    try {
      await this._call({
        type: "deploy_relay/panel/select_source",
        subentry_id: this._selectedProjectId,
        kind,
        ref,
      });
      this._preview = null;
      this._installResult = null;
      this._advancedSourcesOpen = false;
      this._error = "";
      await this._loadState();
    } catch (err) {
      this._error = err?.message || String(err);
      this._setLoading(false);
      this._render();
    }
  }

  async _useRecommended() {
    const recommended = this._sources?.recommended;
    if (!this._selectedProjectId || !recommended?.available) return;

    this._setLoading(true);
    try {
      await this._call({
        type: "deploy_relay/panel/select_source",
        subentry_id: this._selectedProjectId,
        kind: recommended.kind,
        ref: recommended.ref,
      });
      this._preview = null;
      this._installResult = null;
      this._error = "";
      await this._loadState();
    } catch (err) {
      this._error = err?.message || String(err);
      this._setLoading(false);
      this._render();
    }
  }

  async _setMode(mode) {
    if (!this._state || this._modeLoading) return;
    const enabling = mode === "development";
    if (enabling && !window.confirm(this._t("unlockConfirm"))) return;

    this._modeLoading = true;
    this._startProgress("mode", enabling ? this._t("unlockLoading") : this._t("lockLoading"), { start: 12, cap: 90 });
    this._setLoading(true);
    this._render();
    let modeFailed = false;
    try {
      const result = await this._call({
        type: "deploy_relay/panel/set_mode",
        mode,
        confirm: enabling,
      });
      this._state = {
        ...this._state,
        deployment_mode: result.deployment_mode,
        deployment_writes_enabled: result.deployment_writes_enabled,
      };
      this._error = "";
    } catch (err) {
      modeFailed = true;
      this._error = err?.message || String(err);
    } finally {
      this._modeLoading = false;
      this._setLoading(false);
      if (modeFailed) this._cancelProgress();
      else this._finishProgress();
      this._render();
    }
  }

  async _install() {
    if (!this._selectedProjectId || !this._preview || this._installLoading) return;
    if (!this._state?.deployment_writes_enabled) return;
    if (!window.confirm(this._t("installConfirm"))) return;

    const regression = Boolean(this._preview?.version_guard?.regression);
    if (regression && !window.confirm(this._t("regressionConfirm"))) return;

    const recommendation = this._preview?.recommendation;
    const allowUnrecommended = !Boolean(
      recommendation?.available && recommendation?.safe_selected
    );
    if (allowUnrecommended && !window.confirm(this._t("unrecommendedConfirm"))) return;

    this._installLoading = true;
    const installAffected = Number(this._preview?.counts?.add || 0)
      + Number(this._preview?.counts?.change || 0)
      + Number(this._preview?.counts?.remove || 0);
    const installManaged = Number(this._preview?.files?.length || 0);
    this._startProgress(
      "install",
      `${installAffected} Änderung(en) · ${installManaged} verwaltete Datei(en)`,
      { start: 5, cap: 94 }
    );
    this._setLoading(true);
    this._installResult = null;
    let installFailed = false;
    try {
      this._installResult = await this._call({
        type: "deploy_relay/panel/install",
        subentry_id: this._selectedProjectId,
        confirm: true,
        allow_regression: regression,
        allow_unrecommended: allowUnrecommended,
      });
      this._error = "";
      if (this._installResult?.restart_required) {
        const currentProject = this._project();
        if (currentProject) currentProject.restart_pending = true;

        // Re-read the backend state so the visible warning is confirmed by the
        // runtime latch instead of relying only on this browser instance.
        try {
          this._state = await this._call({ type: "deploy_relay/panel/state" });
        } catch {
          // Keep the locally latched warning visible if the state refresh fails.
        }

        window.alert(this._t("restartRequiredDialog"));
      }
    } catch (err) {
      installFailed = true;
      this._error = err?.message || String(err);
    } finally {
      this._installLoading = false;
      this._setLoading(false);
      if (installFailed) this._cancelProgress();
      else this._finishProgress();
      this._render();
    }
  }

  async _loadPreview() {
    if (!this._selectedProjectId || this._previewLoading) return;
    this._previewLoading = true;
    this._startProgress("preview", this._project()?.title || "", { start: 5, cap: 94 });
    this._setLoading(true);
    let previewFailed = false;
    try {
      this._preview = await this._call({
        type: "deploy_relay/panel/preview",
        subentry_id: this._selectedProjectId,
      });
      const managed = Number(this._preview?.files?.length || 0);
      const previewCounts = this._preview?.counts || {};
      const affected = Number(previewCounts.add || 0)
        + Number(previewCounts.change || 0)
        + Number(previewCounts.remove || 0);
      this._setProgress(96, `${managed} verwaltete Datei(en) · ${affected} Änderung(en)`);
      this._error = "";
    } catch (err) {
      previewFailed = true;
      this._preview = null;
      this._error = err?.message || String(err);
    } finally {
      this._previewLoading = false;
      this._setLoading(false);
      if (previewFailed) this._cancelProgress();
      else this._finishProgress();
      this._render();
    }
  }

  async _importProject() {
    const repository = this._importRepo.trim();
    if (!repository) return;

    this._setLoading(true);
    try {
      const project = await this._call({
        type: "deploy_relay/panel/import_project",
        repository,
        manifest_path: this._importManifest.trim() || "deploy-relay.json",
        github_token: this._importToken,
      });
      this._showImport = false;
      this._importToken = "";
      this._importRepo = "";
      this._importManifest = "deploy-relay.json";
      this._selectedProjectId = project.subentry_id;
      this._preview = null;
      this._installResult = null;
      this._restoreResult = null;
      this._sources = null;
      this._error = "";
      await this._loadState();
    } catch (err) {
      this._error = err?.message || String(err);
      this._setLoading(false);
      this._render();
    }
  }

  async _removeProject() {
    const project = this._project();
    if (!project || this._removeConfirmText !== project.title) return;

    this._setLoading(true);
    try {
      await this._call({
        type: "deploy_relay/panel/remove_project",
        subentry_id: project.subentry_id,
        expected_repository: project.repository,
        confirm: true,
      });
      this._showRemove = false;
      this._removeConfirmText = "";
      this._selectedProjectId = null;
      this._sources = null;
      this._preview = null;
      this._installResult = null;
      this._restoreResult = null;
      this._sourceChoice = "";
      this._error = "";
      await this._loadState({ keepProject: false });
    } catch (err) {
      this._error = err?.message || String(err);
      this._setLoading(false);
      this._render();
    }
  }


  async _openBackups() {
    const project = this._project();
    if (!project) return;
    this._showBackups = true;
    this._backupRetention = Number(project.backup_retention || 10);
    this._backupMessage = "";
    this._backups = [];
    this._render();
    await this._loadBackups();
  }

  async _loadBackups() {
    if (!this._selectedProjectId) return;
    this._backupLoading = true;
    this._render();
    try {
      const result = await this._call({
        type: "deploy_relay/panel/backups",
        subentry_id: this._selectedProjectId,
      });
      this._backups = result.backups || [];
      this._backupRetention = Number(result.retention || 10);
      this._backupLimits = {
        minimum: Number(result.minimum || 3),
        maximum: Number(result.maximum || 100),
      };
      this._error = "";
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._backupLoading = false;
      this._render();
    }
  }

  async _saveBackupRetention() {
    const value = Number(this._backupRetention);
    const minimum = Number(this._backupLimits.minimum || 3);
    const maximum = Number(this._backupLimits.maximum || 100);
    if (!Number.isInteger(value) || value < minimum || value > maximum) {
      this._error = this._t("backupRetention") + ": " + minimum + "–" + maximum;
      this._render();
      return;
    }
    if (!window.confirm(this._t("backupRetentionConfirm"))) return;

    this._backupLoading = true;
    this._backupMessage = "";
    this._render();
    try {
      const result = await this._call({
        type: "deploy_relay/panel/set_backup_retention",
        subentry_id: this._selectedProjectId,
        retention: value,
        confirm: true,
      });
      this._backups = result.backups || [];
      this._backupRetention = Number(result.retention || value);
      this._backupMessage = result.cleanup_warning
        ? this._t("backupRetentionSaved") + " " + this._t("backupRetentionCleanupWarning") + " " + result.cleanup_warning
        : this._t("backupRetentionSaved");
      this._state = await this._call({ type: "deploy_relay/panel/state" });
      this._error = "";
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._backupLoading = false;
      this._render();
    }
  }

  async _restoreBackup(transactionId) {
    const project = this._project();
    if (!project || !transactionId || this._restoreLoading) return;
    if (this._state?.deployment_mode !== "development") {
      await this._setMode("development");
      if (this._state?.deployment_mode !== "development") {
        this._backupMessage = this._t("backupRestoreNeedsDevelopment");
        this._render();
        return;
      }
    }
    if (!window.confirm(this._t("backupRestoreConfirm"))) return;

    this._restoreLoading = true;
    const restoreItem = this._backups.find((item) => item.transaction_id === transactionId);
    const restoreFiles = Number(restoreItem?.entries || 0);
    this._startProgress(
      "restore",
      restoreFiles ? `${restoreFiles} Datei(en) im Wiederherstellungspunkt` : (this._project()?.title || ""),
      { start: 5, cap: 94 }
    );
    this._backupMessage = this._t("backupRestoreRunning");
    this._render();
    let restoreFailed = false;
    try {
      const result = await this._call({
        type: "deploy_relay/panel/restore_backup",
        subentry_id: this._selectedProjectId,
        transaction_id: transactionId,
        confirm: true,
      });
      this._restoreResult = result;
      this._installResult = null;
      this._backupMessage = this._t("backupRestoreDone");
      this._state = await this._call({ type: "deploy_relay/panel/state" });
      await this._loadBackups();
      return;
    } catch (err) {
      restoreFailed = true;
      this._error = err?.message || String(err);
    } finally {
      this._restoreLoading = false;
      if (restoreFailed) this._cancelProgress();
      else this._finishProgress();
      this._render();
    }
  }

  _openBatch() {
    const projects = this._state?.projects || [];
    this._batchSelected = new Set(projects.map((item) => item.subentry_id));
    this._batchItems = Object.fromEntries(
      projects.map((item) => [item.subentry_id, { status: "pending" }])
    );
    this._batchMessage = "";
    this._batchPhase = "idle";
    this._batchCheckComplete = false;
    this._batchInstallComplete = false;
    this._batchInstallFailed = false;
    this._batchProgress = { current: 0, total: 0, project: "" };
    this._showBatch = true;
    this._render();
  }

  _batchStatusLabel(status) {
    const labels = {
      pending: "batchPending",
      checking: "batchChecking",
      current: "batchCurrent",
      ready: "batchReady",
      installing: "batchInstalling",
      installed: "batchInstalled",
      installed_restart: "batchInstalledRestart",
      installed_frontend: "batchInstalledFrontend",
      blocker: "batchBlocker",
      error: "batchError",
    };
    return this._t(labels[status] || "batchPending");
  }

  _batchReadyItems() {
    return [...this._batchSelected]
      .map((id) => ({
        project: this._state?.projects?.find((item) => item.subentry_id === id),
        item: this._batchItems[id],
      }))
      .filter(({ project, item }) => project && item?.status === "ready");
  }

  async _batchPreviewSelected() {
    const ids = [...this._batchSelected];
    if (!ids.length) {
      this._batchMessage = this._t("batchNoSelection");
      this._render();
      return;
    }

    this._batchRunning = true;
    this._batchPhase = "checking";
    this._startProgress("batch_check", `0 / ${ids.length} ${this._t("projects")}`, { start: 0, cap: 99, exact: true });
    this._batchCheckComplete = false;
    this._batchInstallComplete = false;
    this._batchInstallFailed = false;
    this._batchMessage = "";
    this._render();

    for (const [batchIndex, id] of ids.entries()) {
      const project = this._state?.projects?.find((item) => item.subentry_id === id);
      this._setProgress(
        ids.length ? (batchIndex / ids.length) * 100 : 0,
        `${batchIndex + 1} / ${ids.length} · ${project?.title || project?.repository || ""}`,
        { exact: true }
      );
      if (!project) continue;
      this._batchItems[id] = { status: "checking" };
      this._render();

      try {
        const sources = await this._call({
          type: "deploy_relay/panel/sources",
          subentry_id: id,
        });
        const recommended = sources?.recommended;
        if (!recommended?.available || !recommended?.explicit_policy) {
          this._batchItems[id] = {
            status: "blocker",
            detail: recommended?.reason || this._t("recommendedUnavailable"),
          };
          continue;
        }

        await this._call({
          type: "deploy_relay/panel/select_source",
          subentry_id: id,
          kind: recommended.kind,
          ref: recommended.ref,
        });

        const preview = await this._call({
          type: "deploy_relay/panel/preview",
          subentry_id: id,
        });
        const counts = preview?.counts || {};
        const affected = Number(counts.add || 0) + Number(counts.change || 0) + Number(counts.remove || 0);
        const safe = Boolean(preview?.recommendation?.available && preview?.recommendation?.safe_selected);
        const regression = Boolean(preview?.version_guard?.regression);

        if (!safe || regression) {
          this._batchItems[id] = {
            status: "blocker",
            preview,
            affected,
            detail: regression ? this._t("versionRegression") : this._t("recommendedDifferent"),
          };
        } else {
          this._batchItems[id] = {
            status: affected > 0 ? "ready" : "current",
            preview,
            affected,
          };
        }
      } catch (err) {
        this._batchItems[id] = {
          status: "error",
          detail: err?.message || String(err),
        };
      }
    }

    try {
      this._state = await this._call({ type: "deploy_relay/panel/state" });
      if (this._selectedProjectId) {
        this._sources = await this._call({
          type: "deploy_relay/panel/sources",
          subentry_id: this._selectedProjectId,
        });
        const activeBatch = this._batchItems[this._selectedProjectId];
        if (activeBatch?.preview) this._preview = activeBatch.preview;
      }
    } catch {
      // Keep the batch results visible even if refreshing state fails.
    }
    this._batchRunning = false;
    this._batchPhase = "idle";
    this._setProgress(100, `${ids.length} / ${ids.length} ${this._t("projects")}`, { exact: true });
    this._finishProgress();
    const blockers = [...this._batchSelected].some((id) => ["blocker", "error"].includes(this._batchItems[id]?.status));
    this._batchCheckComplete = !blockers;
    const ready = this._batchReadyItems().length;
    this._batchMessage = blockers
      ? this._t("batchBlocked")
      : ready === 0
        ? this._t("batchNoUpdates")
        : "";
    this._render();
  }

  async _batchEnableWrites() {
    if (!this._batchCheckComplete) return;
    if (this._state?.deployment_writes_enabled) return;
    if (!window.confirm(this._t("batchUnlockConfirm"))) return;
    this._batchRunning = true;
    this._batchPhase = "unlocking";
    this._render();
    try {
      const result = await this._call({
        type: "deploy_relay/panel/set_mode",
        mode: "development",
        confirm: true,
      });
      this._state = {
        ...this._state,
        deployment_mode: result.deployment_mode,
        deployment_writes_enabled: result.deployment_writes_enabled,
      };
      this._batchMessage = "";
    } catch (err) {
      this._batchMessage = err?.message || String(err);
    } finally {
      this._batchRunning = false;
      this._batchPhase = "idle";
      this._render();
    }
  }

  async _batchInstallSelected() {
    if (!this._batchCheckComplete) return;
    const ready = this._batchReadyItems();
    if (!ready.length || !this._state?.deployment_writes_enabled) return;
    const blockers = [...this._batchSelected].some((id) => ["blocker", "error"].includes(this._batchItems[id]?.status));
    if (blockers) {
      this._batchMessage = this._t("batchBlocked");
      this._render();
      return;
    }

    const prompt = this._t("batchInstallConfirm").replace("{count}", String(ready.length));
    if (!window.confirm(prompt)) return;

    const ordered = [...ready].sort((left, right) => {
      const leftSelf = left.project.project_id === "deploy_relay";
      const rightSelf = right.project.project_id === "deploy_relay";
      return Number(leftSelf) - Number(rightSelf);
    });

    this._batchRunning = true;
    this._batchPhase = "installing";
    this._startProgress("batch_install", `0 / ${ordered.length} ${this._t("projects")}`, { start: 0, cap: 99, exact: true });
    this._batchInstallComplete = false;
    this._batchInstallFailed = false;
    this._batchMessage = "";
    this._batchProgress = { current: 0, total: ordered.length, project: "" };
    this._render();
    let failed = false;

    for (const [index, { project }] of ordered.entries()) {
      this._batchProgress = { current: index + 1, total: ordered.length, project: project.title || project.repository || "" };
      this._setProgress(
        ordered.length ? (index / ordered.length) * 100 : 0,
        `${index + 1} / ${ordered.length} · ${project.title || project.repository || ""}`,
        { exact: true }
      );
      const id = project.subentry_id;
      this._batchItems[id] = { ...this._batchItems[id], status: "installing" };
      this._render();
      try {
        const result = await this._call({
          type: "deploy_relay/panel/install",
          subentry_id: id,
          confirm: true,
          allow_regression: false,
          allow_unrecommended: false,
        });
        this._batchItems[id] = {
          ...this._batchItems[id],
          status: result?.restart_required ? "installed_restart" : result?.lifecycle === "frontend_reload" ? "installed_frontend" : "installed",
          result,
        };
      } catch (err) {
        this._batchItems[id] = {
          ...this._batchItems[id],
          status: "error",
          detail: err?.message || String(err),
        };
        failed = true;
        break;
      }
    }

    try {
      this._state = await this._call({ type: "deploy_relay/panel/state" });
    } catch {
      // The loaded DRA runtime remains usable until the final HA restart.
    }
    this._batchRunning = false;
    this._batchPhase = "idle";
    if (failed) this._cancelProgress();
    else {
      this._setProgress(100, `${ordered.length} / ${ordered.length} ${this._t("projects")}`, { exact: true });
      this._finishProgress();
    }
    this._batchInstallComplete = !failed;
    this._batchInstallFailed = failed;
    const batchResults = [...this._batchSelected]
      .map((id) => this._batchItems[id]?.result)
      .filter(Boolean);
    const batchRestartRequired = (this._state?.projects || []).some((item) => item.restart_pending)
      || batchResults.some((item) => item.restart_required);
    const batchFrontendReloadRequired = !batchRestartRequired
      && batchResults.some((item) => item.lifecycle === "frontend_reload");
    this._batchMessage = failed
      ? this._t("batchPartial")
      : batchRestartRequired
        ? this._t("batchRestartSummary")
        : batchFrontendReloadRequired
          ? this._t("batchFrontendSummary")
          : this._t("batchDoneSummary");
    this._render();
  }

  _project() {
    return this._state?.projects?.find(
      (project) => project.subentry_id === this._selectedProjectId
    );
  }

  _navigate(path) {
    history.pushState(null, "", path);
    window.dispatchEvent(new Event("location-changed"));
  }

  _setLoading(value) {
    this._loading = value;
    this._render();
  }

  _operationLabel(operation) {
    return this._t(operation);
  }

  _scrollToWorkflowTarget(selector, focusSelector = null) {
    const target = this.shadowRoot?.querySelector(selector);
    if (!target) return;
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    if (focusSelector) {
      window.setTimeout(() => {
        this.shadowRoot?.querySelector(focusSelector)?.focus?.({ preventScroll: true });
      }, 350);
    }
  }

  _handleWorkflowStep(step) {
    const project = this._project();

    if (step === 1) {
      this._scrollToWorkflowTarget("#source-card");
      return;
    }

    if (step === 2) {
      if (!project?.selected_source_commit) {
        this._scrollToWorkflowTarget("#source-card", "#use-recommended");
        return;
      }
      this._scrollToWorkflowTarget("#preview-card", "#load-preview");
      if (!this._preview && !this._previewLoading) {
        void this._loadPreview();
      }
      return;
    }

    if (step === 3) {
      this._scrollToWorkflowTarget("#preview-card", "#mode-toggle");
      return;
    }

    if (step === 4) {
      this._scrollToWorkflowTarget("#preview-card", "#install-project");
    }
  }

  _filteredFiles() {
    if (!this._preview) return [];
    const search = this._search.trim().toLowerCase();
    return this._preview.files.filter((file) => {
      if (this._filter !== "all" && file.operation !== this._filter) return false;
      if (search && !file.target_path.toLowerCase().includes(search)) return false;
      return true;
    });
  }

  _render() {
    if (!this.shadowRoot) return;

    // The diagnostics panel owns its own data/load state. Preserve the same
    // custom-element instance across parent renders so progress updates in the
    // main DRA UI do not restart diagnostics loading.
    const preservedDiagnosticsPanel =
      this.shadowRoot.querySelector("#diagnostics-panel");

    const project = this._project();
    const counts = this._preview?.counts ?? {
      add: 0,
      change: 0,
      remove: 0,
      unchanged: 0,
    };
    const development = this._state?.deployment_mode === "development";
    const affected = counts.add + counts.change + counts.remove;
    const installLabel = affected === 1
      ? this._t("installOne")
      : this._t("installMany").replace("{count}", String(affected));
    const versionGuard = this._preview?.version_guard ?? null;
    const recommendation = this._sources?.recommended ?? this._preview?.recommendation ?? null;
    const restartPendingProjects = (this._state?.projects || []).filter(
      (item) => item.restart_pending
    );
    const restartPending = restartPendingProjects.length > 0;
    const currentRestartPending = Boolean(
      project?.restart_pending ||
      this._installResult?.restart_required ||
      this._restoreResult?.restart_required
    );
    const currentFrontendReload = Boolean(
      (
        this._installResult?.lifecycle === "frontend_reload" ||
        this._restoreResult?.lifecycle === "frontend_reload"
      ) && !currentRestartPending
    );
    const previewLifecycle = this._preview?.lifecycle?.effective || null;
    const previewLifecycleLabel = previewLifecycle === "frontend_reload"
      ? this._t("lifecycleFrontend")
      : previewLifecycle === "home_assistant_restart"
        ? this._t("lifecycleRestart")
        : this._t("lifecycleNone");
    const previewLifecycleCompact = previewLifecycle === "frontend_reload"
      ? this._t("lifecycleCompactFrontend")
      : previewLifecycle === "home_assistant_restart"
        ? this._t("lifecycleCompactRestart")
        : this._t("lifecycleCompactNone");
    const sourceSelected = Boolean(project?.selected_source_commit);
    const sourceSelectionPending = this._sourceSelectionIsPending();
    const recommendedSelected = Boolean(
      recommendation?.available ? recommendation.safe_selected : sourceSelected
    );
    const previewReady = Boolean(this._preview);
    const installDone = Boolean(this._installResult);
    const noChanges = previewReady && affected === 0;
    const installReady = Boolean(
      this._preview
      && development
      && affected > 0
      && !this._previewLoading
      && !this._modeLoading
      && !this._installLoading
    );
    const nextStep = currentRestartPending
      ? this._t("nextRestart")
      : currentFrontendReload
        ? this._t("nextFrontendReload")
        : installDone
          ? this._t("nextDone")
          : !project
        ? this._t("nextProject")
        : !recommendedSelected
          ? this._t("nextSource")
          : !previewReady
            ? this._t("nextPreview")
            : noChanges
              ? this._t("noChangesNext")
              : !development
                ? this._t("nextUnlock")
                : this._t("nextInstall");

    const batchSelectedCount = this._batchSelected.size;
    const batchReadyCount = this._batchReadyItems().length;
    const batchHasBlockers = [...this._batchSelected].some((id) => ["blocker", "error"].includes(this._batchItems[id]?.status));
    const batchCheckRunning = this._batchPhase === "checking";
    const batchInstallRunning = this._batchPhase === "installing";
    const batchInstallReady = Boolean(
      !this._batchRunning
      && !this._batchInstallComplete
      && this._batchCheckComplete
      && batchReadyCount > 0
      && !batchHasBlockers
      && development
    );
    const batchCheckLabel = batchCheckRunning
      ? this._t("batchCheckRunning")
      : this._batchCheckComplete
        ? this._t("batchCheckDone")
        : this._t("batchCheck");
    const batchInstalledResults = [...this._batchSelected]
      .map((id) => this._batchItems[id]?.result)
      .filter(Boolean);
    const batchNeedsRestart = restartPending
      || batchInstalledResults.some((item) => item.restart_required);
    const batchNeedsFrontendReload = !batchNeedsRestart
      && batchInstalledResults.some((item) => item.lifecycle === "frontend_reload");
    const batchInstallLabel = batchInstallRunning
      ? this._t("batchInstallRunning")
          .replace("{current}", String(this._batchProgress.current))
          .replace("{total}", String(this._batchProgress.total))
          .replace("{project}", this._batchProgress.project)
      : this._batchInstallComplete
        ? this._t("batchInstallDone")
        : `${batchReadyCount} ${this._t("batchInstall")}`;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100%;
          min-width: 0;
          max-width: 100%;
          overflow-x: hidden;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        }
        * { box-sizing: border-box; }
        .app {
          min-height: 100vh;
          min-width: 0;
          max-width: 100%;
          overflow-x: clip;
          container-type: inline-size;
          container-name: relay-app;
        }
        .topbar {
          position: sticky; top: 0; z-index: 20;
          display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
          padding: 14px 20px;
          background: var(--app-header-background-color, var(--card-background-color));
          color: var(--app-header-text-color, var(--primary-text-color));
          border-bottom: 1px solid var(--divider-color);
        }
        .brand { flex: 1; min-width: 0; }
        .brand h1 { margin: 0; font-size: 22px; line-height: 1.2; }
        .brand small { color: var(--secondary-text-color); }
        .badge {
          border-radius: 999px; padding: 6px 10px; font-size: 12px; font-weight: 700;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
        }
        .badge.locked { color: var(--warning-color, #f3b200); }
        .badge.development { color: var(--error-color, #db4437); border-color: var(--error-color, #db4437); }
        .layout {
          display: grid;
          grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
          min-height: calc(100vh - 72px);
        }
        .rail {
          border-right: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
          padding: 16px;
        }
        .rail-head {
          margin-bottom: 10px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        .rail-head h2 { margin: 0; font-size: 16px; }
        .rail-head .danger {
          min-height: 34px;
          padding: 6px 9px;
          font-size: 12px;
          flex: 0 0 auto;
        }
        .project-picker { display: grid; gap: 8px; min-width: 0; }
        .project-picker select { width: 100%; min-width: 0; }
        .selected-project-repo {
          min-width: 0; color: var(--secondary-text-color); font-size: 12px;
          overflow-wrap: anywhere;
        }
        .project-actions {
          display: grid;
          grid-template-columns: 1fr;
          gap: 8px;
        }
        .project-actions button {
          width: 100%;
          min-width: 0;
          min-height: 46px;
          padding: 10px 12px;
          white-space: normal;
          line-height: 1.25;
        }
        .batch-list { display: grid; gap: 8px; margin: 14px 0; }
        .backup-list { display: grid; gap: 8px; margin: 14px 0; max-height: 48vh; overflow: auto; }
        .backup-item {
          display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 10px;
          align-items: center; padding: 11px; border: 1px solid var(--divider-color);
          border-radius: 10px; min-width: 0;
        }
        .backup-main { min-width: 0; display: grid; gap: 3px; }
        .backup-main small { color: var(--secondary-text-color); overflow-wrap: anywhere; }
        .backup-retention-row {
          display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 10px; align-items: end;
          margin: 14px 0;
        }
        .backup-retention-row input { width: 100%; min-width: 0; }
        .backup-kind { font-weight: 700; }
        .batch-item {
          display: grid; grid-template-columns: auto minmax(0,1fr) auto; gap: 10px;
          align-items: start; padding: 10px; border: 1px solid var(--divider-color);
          border-radius: 10px; min-width: 0;
        }
        .batch-item input[type="checkbox"] { width: 18px; height: 18px; min-height: 0; margin-top: 2px; }
        .batch-item-main { min-width: 0; }
        .batch-item-main strong, .batch-item-main small { display: block; overflow-wrap: anywhere; }
        .batch-item-main small { color: var(--secondary-text-color); margin-top: 2px; }
        .batch-status { font-size: 12px; font-weight: 700; text-align: right; }
        .batch-status.ready, .batch-status.current, .batch-status.installed, .batch-status.installed_restart, .batch-status.installed_frontend { color: var(--success-color, #2e7d32); }
        .batch-status.checking, .batch-status.installing { color: var(--warning-color, #f3b200); }
        .batch-status.checking::before,
        .batch-status.installing::before {
          content: "";
          display: inline-block;
          width: 10px;
          height: 10px;
          margin-right: 5px;
          border: 2px solid currentColor;
          border-right-color: transparent;
          border-radius: 50%;
          vertical-align: -1px;
          animation: relay-spin .8s linear infinite;
        }
        .batch-status.ready::before,
        .batch-status.current::before,
        .batch-status.installed::before,
        .batch-status.installed_restart::before,
        .batch-status.installed_frontend::before {
          content: "✓ ";
          font-weight: 900;
        }
        .batch-status.blocker, .batch-status.error { color: var(--error-color, #db4437); }
        .batch-detail { margin-top: 4px; color: var(--secondary-text-color); font-size: 11px; overflow-wrap: anywhere; }
        .batch-note { margin: 10px 0; font-size: 12px; color: var(--secondary-text-color); }
        .batch-message { margin: 10px 0; padding: 10px; border: 1px solid var(--divider-color); border-radius: 9px; overflow-wrap: anywhere; }
        .operation-progress {
          margin: 0 0 14px;
          padding: 11px 12px;
          border: 1px solid color-mix(in srgb, var(--primary-color) 45%, var(--divider-color));
          border-radius: 10px;
          background: color-mix(in srgb, var(--primary-color) 8%, var(--card-background-color));
          min-width: 0;
        }
        .operation-progress-head {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          gap: 10px;
          margin-bottom: 7px;
        }
        .operation-progress-head span {
          flex: 0 0 auto;
          font-weight: 800;
          color: var(--primary-color);
        }
        .operation-progress-track {
          height: 10px;
          overflow: hidden;
          border-radius: 999px;
          background: color-mix(in srgb, var(--divider-color) 70%, transparent);
        }
        .operation-progress-fill {
          height: 100%;
          border-radius: inherit;
          background: var(--primary-color);
          transition: width .28s ease;
        }
        .operation-progress small {
          display: block;
          margin-top: 6px;
          color: var(--secondary-text-color);
          overflow-wrap: anywhere;
        }
        .modal.wide { width: min(760px, 100%); position: relative; }
        .modal-close {
          position: absolute;
          top: 10px;
          right: 10px;
          width: 34px;
          height: 34px;
          min-height: 34px;
          padding: 0;
          border-radius: 50%;
          font-size: 22px;
          line-height: 1;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        .batch-action-running {
          position: relative;
          overflow: hidden;
          background: var(--warning-color, #f3b200) !important;
          border-color: var(--warning-color, #f3b200) !important;
          color: var(--primary-background-color, #111) !important;
          opacity: 1 !important;
          cursor: progress !important;
        }
        .batch-action-running::after {
          content: "";
          position: absolute;
          inset: 0;
          transform: translateX(-110%);
          background: linear-gradient(90deg, transparent, rgba(255,255,255,.28), transparent);
          animation: relay-preview-sheen 1.15s ease-in-out infinite;
          pointer-events: none;
        }
        .batch-action-success {
          background: var(--success-color, #2e7d32) !important;
          border-color: var(--success-color, #2e7d32) !important;
          color: white !important;
          opacity: 1 !important;
        }
        .content { padding: 20px; min-width: 0; max-width: 100%; overflow-x: hidden; }
        .grid {
          display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 16px; margin-bottom: 16px;
        }
        .card {
          background: var(--card-background-color);
          border: 1px solid var(--divider-color);
          border-radius: 14px;
          padding: 18px;
          box-shadow: var(--ha-card-box-shadow, none);
          min-width: 0;
        }
        .card h2 { margin: 0 0 14px; font-size: 18px; }
        .workflow-guide {
          margin-bottom: 16px; padding: 14px; min-width: 0;
          border: 1px solid var(--divider-color); border-radius: 12px;
          background: var(--card-background-color);
        }
        .workflow-guide h2 { margin: 0; font-size: 16px; }
        .workflow-hint { margin-top: 4px; color: var(--secondary-text-color); font-size: 12px; }
        .workflow-steps {
          display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 8px; margin-top: 12px;
        }
        .workflow-step {
          min-width: 0; padding: 9px 10px; border: 1px solid var(--divider-color);
          border-radius: 10px; background: var(--secondary-background-color);
          color: var(--secondary-text-color); font-size: 12px; font-weight: 700;
          overflow-wrap: anywhere;
        }
        .workflow-step:hover { filter: brightness(1.08); }
        .workflow-step:focus-visible {
          outline: 2px solid var(--primary-color);
          outline-offset: 2px;
        }
        .workflow-target { scroll-margin-top: 92px; }
        .workflow-step.current {
          border-color: var(--primary-color); color: var(--primary-text-color);
          background: color-mix(in srgb, var(--primary-color) 12%, var(--secondary-background-color));
        }
        .workflow-step.done { border-color: var(--success-color, #2e7d32); color: var(--success-color, #2e7d32); }
        .workflow-next {
          margin-top: 10px; padding: 9px 10px; border-radius: 9px;
          background: color-mix(in srgb, var(--primary-color) 10%, transparent);
          font-weight: 700; overflow-wrap: anywhere;
        }
        .guided-actions {
          display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px; margin-top: 12px;
        }
        .guided-actions button { width: 100%; min-width: 0; white-space: normal; }
        .project-restart-pending {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          margin: -2px 0 14px;
          padding: 7px 10px;
          border-radius: 9px;
          border: 1px solid var(--warning-color, #f3b200);
          background: color-mix(in srgb, var(--warning-color, #f3b200) 14%, transparent);
          color: var(--warning-color, #f3b200);
          font-weight: 700;
        }
        .meta { display: grid; grid-template-columns: 140px 1fr; gap: 8px 12px; font-size: 14px; }
        .meta .key { color: var(--secondary-text-color); }
        .meta .value { overflow-wrap: anywhere; }
        .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        button, select, input {
          font: inherit;
        }
        button {
          border: 1px solid var(--divider-color);
          border-radius: 9px;
          padding: 9px 13px;
          max-width: 100%;
          overflow-wrap: anywhere;
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          cursor: pointer;
        }
        button.primary {
          background: var(--primary-color);
          border-color: var(--primary-color);
          color: var(--text-primary-color, white);
        }
        button.danger {
          border-color: var(--error-color, #db4437);
          color: var(--error-color, #db4437);
        }
        button.install-ready {
          background: #d4a017;
          border-color: #f0c85a;
          color: #111111;
          font-size: 15px;
          font-weight: 850;
          letter-spacing: .01em;
          box-shadow: 0 0 0 1px rgba(240, 200, 90, .22), 0 4px 14px rgba(212, 160, 23, .18);
        }
        button.install-ready:hover {
          background: #e0ae22;
          border-color: #f6d477;
          color: #0b0b0b;
          filter: brightness(1.03);
        }
        button.install-ready:focus-visible {
          outline: 2px solid #f6d477;
          outline-offset: 2px;
        }
        button:disabled { opacity: .5; cursor: default; }
        button.preview-loading,
        button.mode-loading,
        button.install-loading {
          position: relative;
          overflow: hidden;
          background: var(--warning-color, #f3b200);
          border-color: var(--warning-color, #f3b200);
          color: var(--primary-background-color, #111);
          cursor: progress;
        }
        button.preview-loading:disabled,
        button.mode-loading:disabled,
        button.install-loading:disabled { opacity: 1; cursor: progress; }
        button.preview-ready {
          background: var(--success-color, #2e7d32);
          border-color: var(--success-color, #2e7d32);
          color: white;
          display: inline-flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 2px;
          line-height: 1.15;
        }
        button.preview-ready .preview-checksum,
        button.preview-ready .preview-lifecycle-compact {
          font-size: 11px;
          font-weight: 700;
          opacity: .92;
        }
        button.preview-ready .preview-lifecycle-compact {
          margin-top: 1px;
          white-space: normal;
          text-align: center;
        }
        button.preview-ready:hover {
          background: color-mix(in srgb, var(--success-color, #2e7d32) 88%, black);
          border-color: color-mix(in srgb, var(--success-color, #2e7d32) 88%, black);
        }
        .preview-ready-hint {
          margin-top: 10px;
          padding: 9px 10px;
          border: 1px solid color-mix(in srgb, var(--success-color, #2e7d32) 55%, transparent);
          border-radius: 9px;
          background: color-mix(in srgb, var(--success-color, #2e7d32) 12%, transparent);
          color: var(--primary-text-color);
          font-size: 13px;
          font-weight: 700;
          overflow-wrap: anywhere;
        }
        .preview-integrity {
          display: flex;
          flex-wrap: wrap;
          gap: 4px 10px;
          margin-top: 6px;
          font-size: 12px;
        }
        .preview-integrity span {
          color: var(--secondary-text-color);
          font-weight: 500;
        }
        button.preview-loading::after,
        button.mode-loading::after,
        button.install-loading::after {
          content: "";
          position: absolute;
          inset: 0;
          transform: translateX(-110%);
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,.38),
            transparent
          );
          animation: relay-preview-sheen 1.15s ease-in-out infinite;
          pointer-events: none;
        }
        .button-spinner {
          display: inline-block;
          width: 14px;
          height: 14px;
          margin-right: 7px;
          border: 2px solid currentColor;
          border-right-color: transparent;
          border-radius: 50%;
          vertical-align: -2px;
          animation: relay-spin .8s linear infinite;
        }
        .preview-progress,
        .mode-progress,
        .install-progress {
          position: relative;
          height: 4px;
          margin: 12px 0 2px;
          overflow: hidden;
          border-radius: 999px;
          background: color-mix(in srgb, var(--warning-color, #f3b200) 24%, transparent);
        }
        .preview-progress::after,
        .mode-progress::after,
        .install-progress::after {
          content: "";
          position: absolute;
          inset: 0 auto 0 0;
          width: 42%;
          border-radius: inherit;
          background: var(--warning-color, #f3b200);
          animation: relay-preview-bar 1.05s ease-in-out infinite;
        }
        .mode-working,
        .install-working {
          margin: 10px 0 2px;
          padding: 10px 12px;
          border: 1px solid color-mix(in srgb, var(--warning-color, #f3b200) 58%, transparent);
          border-radius: 10px;
          background: color-mix(in srgb, var(--warning-color, #f3b200) 12%, transparent);
          color: var(--primary-text-color);
          font-size: 13px;
          font-weight: 700;
          overflow-wrap: anywhere;
        }
        .frontend-reload-required {
          margin: 12px 0;
          padding: 14px;
          border: 2px solid var(--primary-color);
          border-radius: 12px;
          background: color-mix(in srgb, var(--primary-color) 12%, transparent);
        }
        .frontend-reload-required strong { display: block; margin-bottom: 6px; }
        .frontend-reload-required button { margin-top: 10px; width: 100%; }
        .preview-lifecycle {
          margin-top: 7px;
          font-size: 12px;
          color: var(--secondary-text-color);
        }
        .preview-lifecycle strong { color: var(--primary-text-color); }
        .top-restart-badge {
          color: var(--warning-color, #f3b200);
          border-color: var(--warning-color, #f3b200);
          background: color-mix(in srgb, var(--warning-color, #f3b200) 12%, var(--secondary-background-color));
          white-space: nowrap;
        }
        @keyframes relay-spin {
          to { transform: rotate(360deg); }
        }
        @keyframes relay-preview-sheen {
          55%, 100% { transform: translateX(110%); }
        }
        @keyframes relay-preview-bar {
          0% { transform: translateX(-110%); }
          55% { transform: translateX(85%); }
          100% { transform: translateX(245%); }
        }
        select, input {
          min-height: 40px;
          border: 1px solid var(--divider-color);
          border-radius: 9px;
          padding: 8px 10px;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
        }
        select { flex: 1; min-width: 210px; }
        input[type="text"] { flex: 1; min-width: 180px; }
        .notice {
          margin-bottom: 16px; border-radius: 10px; padding: 12px 14px;
          background: color-mix(in srgb, var(--warning-color, #f3b200) 12%, transparent);
          border: 1px solid color-mix(in srgb, var(--warning-color, #f3b200) 40%, transparent);
          overflow-wrap: anywhere;
        }
        .restart-required, .success, .recommendation, .footer-note, code {
          max-width: 100%; overflow-wrap: anywhere; word-break: break-word;
        }
        .error {
          margin-bottom: 16px; border-radius: 10px; padding: 12px 14px;
          color: var(--error-color); border: 1px solid var(--error-color);
        }
        .success {
          margin-bottom: 16px; border-radius: 10px; padding: 12px 14px;
          color: var(--success-color, #2e7d32); border: 1px solid var(--success-color, #2e7d32);
        }
        .restart-required {
          margin-bottom: 16px;
          border-radius: 12px;
          padding: 16px;
          border: 2px solid var(--warning-color, #f3b200);
          background: color-mix(in srgb, var(--warning-color, #f3b200) 18%, var(--card-background-color, #111));
          color: var(--primary-text-color);
          box-shadow: 0 0 0 1px color-mix(in srgb, var(--warning-color, #f3b200) 25%, transparent);
        }
        .restart-required strong {
          display: block;
          color: var(--warning-color, #f3b200);
          font-size: 16px;
          letter-spacing: .04em;
          margin-bottom: 7px;
        }
        .restart-required .restart-action {
          margin-top: 9px;
          font-weight: 700;
        }
        .version-check {
          margin: 14px 0; border-radius: 10px; padding: 12px 14px;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
        }
        .version-check.warning {
          border-color: var(--warning-color, #f3b200);
        }
        .version-check.regression {
          border-color: var(--error-color, #db4437);
          color: var(--error-color, #db4437);
          background: color-mix(in srgb, var(--error-color, #db4437) 8%, transparent);
        }
        .version-meta {
          display:grid; grid-template-columns: 120px 1fr; gap:6px 10px;
          margin-top:8px; font-size:13px;
        }
        .version-meta .key { color: var(--secondary-text-color); }
        .recommendation {
          margin: 0 0 14px;
          border: 1px solid var(--success-color, #2e7d32);
          border-radius: 12px;
          padding: 14px;
          background: color-mix(in srgb, var(--success-color, #2e7d32) 8%, transparent);
        }
        .recommendation.warning {
          border-color: var(--warning-color, #f3b200);
          background: color-mix(in srgb, var(--warning-color, #f3b200) 8%, transparent);
        }
        .recommendation.error {
          border-color: var(--error-color, #db4437);
          background: color-mix(in srgb, var(--error-color, #db4437) 8%, transparent);
        }
        .recommendation h3 { margin: 0 0 8px; font-size: 16px; }
        details.advanced {
          margin-top: 14px;
          border-top: 1px solid var(--divider-color);
          padding-top: 12px;
        }
        details.advanced > summary {
          cursor: pointer;
          font-weight: 650;
        }
        .summary {
          display: grid; grid-template-columns: repeat(4, minmax(80px, 1fr));
          gap: 10px; margin-bottom: 14px;
        }
        .preview-summary {
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 7px;
          margin: 8px 0 0;
        }
        .stat {
          border: 1px solid var(--divider-color); border-radius: 10px;
          padding: 11px; text-align: center;
        }
        .stat b { display: block; font-size: 22px; }
        .preview-stat {
          min-width: 0;
          padding: 8px 5px;
          line-height: 1.05;
          background: var(--secondary-background-color);
        }
        .preview-stat b { font-size: 20px; line-height: 1; }
        .preview-stat .stat-label {
          display: block;
          margin-top: 4px;
          font-size: 11px;
          font-weight: 750;
          overflow-wrap: anywhere;
        }
        .preview-stat.add,
        .preview-stat.change,
        .preview-stat.remove {
          font-weight: 750;
        }
        .preview-stat.add.active {
          border-color: var(--success-color, #2e7d32);
          background: color-mix(in srgb, var(--success-color, #2e7d32) 10%, var(--secondary-background-color));
        }
        .preview-stat.change.active {
          border-color: var(--warning-color, #f3b200);
          background: color-mix(in srgb, var(--warning-color, #f3b200) 12%, var(--secondary-background-color));
        }
        .preview-stat.remove.active {
          border-color: var(--error-color, #db4437);
          background: color-mix(in srgb, var(--error-color, #db4437) 10%, var(--secondary-background-color));
        }
        .preview-stat.unchanged {
          opacity: .66;
          font-weight: 500;
        }
        .preview-lifecycle-banner {
          margin-top: 8px;
          padding: 8px 10px;
          border-radius: 9px;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
          font-size: 12px;
          overflow-wrap: anywhere;
        }
        .preview-lifecycle-banner strong { color: var(--primary-text-color); }
        .toolbar {
          display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
          margin: 12px 0;
        }
        .toolbar input { min-width: 240px; }
        .filter.active { border-color: var(--primary-color); color: var(--primary-color); }
        .table-wrap { overflow: auto; max-height: 58vh; border: 1px solid var(--divider-color); border-radius: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 10px 12px; border-bottom: 1px solid var(--divider-color); text-align: left; vertical-align: top; }
        th { position: sticky; top: 0; background: var(--card-background-color); z-index: 2; }
        td.path { min-width: 320px; font-family: var(--code-font-family, monospace); }
        td.hash { font-family: var(--code-font-family, monospace); font-size: 11px; }
        .op { font-weight: 700; white-space: nowrap; }
        .op.add { color: var(--success-color, #2e7d32); }
        .op.change { color: var(--warning-color, #f3b200); }
        .op.remove { color: var(--error-color, #db4437); }
        .op.unchanged { color: var(--secondary-text-color); }
        .empty { color: var(--secondary-text-color); padding: 20px 0; }
        .spinner { opacity: .72; }
        .footer-note { color: var(--secondary-text-color); font-size: 12px; margin-top: 10px; }
        .modal-backdrop {
          position: fixed; inset: 0; z-index: 100;
          display: grid; place-items: center;
          padding: 20px;
          background: rgba(0, 0, 0, .55);
        }
        .modal {
          width: min(620px, 100%);
          background: var(--card-background-color);
          border: 1px solid var(--divider-color);
          border-radius: 16px;
          padding: 20px;
          box-shadow: 0 18px 60px rgba(0,0,0,.35);
        }
        .modal h2 { margin: 0 0 16px; }
        .modal-warning {
          margin: 0 0 14px; padding: 12px;
          border: 1px solid var(--error-color, #db4437); border-radius: 10px;
          color: var(--primary-text-color); overflow-wrap: anywhere;
        }
        .field { display: grid; gap: 6px; margin-bottom: 14px; }
        .field label { color: var(--secondary-text-color); font-size: 13px; }
        .field input { width: 100%; }
        .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }

        @container relay-app (max-width: 1180px) {
          .layout { grid-template-columns: 1fr; }
          .rail {
            border-right: 0;
            border-bottom: 1px solid var(--divider-color);
            padding: 12px 14px;
          }
          .rail-head { margin-bottom: 8px; }
          .project-picker { grid-template-columns: minmax(0, 1fr); }
          .project-actions { grid-template-columns: 1fr; }
          .grid { grid-template-columns: 1fr; }
          .content { padding: 14px; }
          .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .summary.preview-summary { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        }
        @container relay-app (max-width: 760px) {
          .topbar {
            padding: 10px 12px;
            gap: 8px;
          }
          .brand { flex: 1 0 100%; }
          .brand h1 { font-size: 20px; }
          .brand small { display: none; }
          .topbar #refresh { flex: 1 1 100%; }
          .rail { padding: 10px 12px; }
          .rail-head h2 { font-size: 14px; }
          .content { padding: 10px; }
          .card { padding: 14px; border-radius: 12px; }
          .meta {
            grid-template-columns: 1fr;
            gap: 3px;
            font-size: 13px;
          }
          .meta .key {
            margin-top: 6px;
            font-size: 11px;
            font-weight: 700;
          }
          .row { gap: 8px; min-width: 0; }
          .workflow-steps { grid-template-columns: 1fr; }
          .workflow-step { padding: 8px 10px; }
          .workflow-next { font-size: 13px; line-height: 1.35; white-space: normal; }
          .workflow-next .workflow-next-lifecycle {
            display: block;
            margin-top: 3px;
            font-size: 12px;
            font-weight: 700;
            opacity: .92;
          }
          .guided-actions { grid-template-columns: 1fr; }
          .project-actions { grid-template-columns: 1fr; }
          .backup-item { grid-template-columns: 1fr; }
          .backup-item button { width: 100%; }
          .backup-retention-row { grid-template-columns: 1fr; }
          .backup-retention-row button { width: 100%; }
          .recommendation .row button, #project-config { width: 100%; }
          select { min-width: 0; width: 100%; }
          input[type="text"] { min-width: 0; width: 100%; }
          .toolbar input { min-width: 0; width: 100%; }
          .summary { gap: 7px; }
          .summary.preview-summary { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 5px; }
          .stat { padding: 9px 6px; }
          .stat b { font-size: 19px; }
          .preview-stat { padding: 7px 3px; }
          .preview-stat b { font-size: 18px; }
          .preview-stat .stat-label { font-size: 10px; }
          .modal-backdrop {
            padding: 10px;
          }
          .modal.wide {
            width: 100%;
            max-height: calc(100dvh - 20px);
            overflow: auto;
            padding: 16px;
            border-radius: 14px;
          }
          .batch-actions {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            grid-template-areas:
              "check unlock"
              "install close";
            gap: 10px;
            width: 100%;
          }
          .batch-actions button {
            width: 100%;
            min-width: 0;
            min-height: 54px;
            padding: 10px 12px;
            line-height: 1.25;
            white-space: normal;
            word-break: normal;
            overflow-wrap: break-word;
          }
          .batch-actions #batch-check { grid-area: check; }
          .batch-actions #batch-unlock { grid-area: unlock; }
          .batch-actions #batch-install { grid-area: install; }
          .batch-actions #batch-close { grid-area: close; }
          .batch-actions #batch-reload {
            grid-column: 1 / -1;
            min-height: 48px;
          }
        }

        /* Viewport fallback for browsers without container-query support. */
        @media (max-width: 900px) {
          .layout { grid-template-columns: 1fr; }
          .rail { border-right: 0; border-bottom: 1px solid var(--divider-color); }
          .project-picker { grid-template-columns: 1fr; }
          .grid { grid-template-columns: 1fr; }
          .content { padding: 12px; }
          .topbar { padding: 12px; }
          .summary { grid-template-columns: repeat(2, 1fr); }
          .summary.preview-summary { grid-template-columns: repeat(4, minmax(0, 1fr)); }
          .batch-actions {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            grid-template-areas:
              "check unlock"
              "install close";
            gap: 10px;
          }
          .batch-actions button {
            width: 100%;
            min-width: 0;
            white-space: normal;
            word-break: normal;
          }
          .batch-actions #batch-check { grid-area: check; }
          .batch-actions #batch-unlock { grid-area: unlock; }
          .batch-actions #batch-install { grid-area: install; }
          .batch-actions #batch-close { grid-area: close; }
          .batch-actions #batch-reload { grid-column: 1 / -1; }
        }
      </style>

      <div class="app">
        <header class="topbar">
          <div class="brand">
            <h1>DEPLOY RELAY AGENT</h1>
            <small>${esc(this._t("subtitle"))}</small>
          </div>
          <span class="badge ${development ? "development" : "locked"}">${esc(development ? this._t("development") : this._t("locked"))}</span>
          <span class="badge">v${esc(this._state?.version || "—")}</span>
          ${restartPending ? `
            <span class="badge top-restart-badge" role="status" aria-live="polite"
                  title="${esc(this._t("restartRequired"))}">
              ⚠ ${esc(this._t("restartPendingTop"))}${restartPendingProjects.length > 1 ? ` · ${restartPendingProjects.length}` : ""}
            </span>
          ` : ""}
          <button id="refresh">${esc(this._t("refresh"))}</button>
        </header>

        <div class="layout">
          <aside class="rail">
            <div class="rail-head">
              <h2>${esc(this._t("project"))}</h2>
              <button class="danger" id="remove-project" ${project && !this._initializing && !this._loading ? "" : "disabled"}>${esc(this._t("removeProject"))}</button>
            </div>
            <div class="project-picker">
              <select id="project-select" aria-label="${esc(this._t("selectProject"))}" ${(this._state?.projects || []).length && !this._initializing && !this._loading ? "" : "disabled"}>
                ${(this._state?.projects || []).map((item) => `
                  <option value="${esc(item.subentry_id)}" ${item.subentry_id === this._selectedProjectId ? "selected" : ""}>
                    ${item.restart_pending ? "⚠ " : ""}${esc(item.title)}
                  </option>
                `).join("") || `<option>${esc(this._t("noProjects"))}</option>`}
                ${(this._state?.projects || []).length ? `
                  <option value="__batch_separator__" disabled>────────────</option>
                  <option value="__batch_update__">⇄ ${esc(this._t("batchUpdate"))}</option>
                ` : ""}
              </select>
              ${project ? `<div class="selected-project-repo">${esc(project.repository)}</div>` : ""}
              <div class="project-actions">
                <button class="primary" id="import-project" ${this._initializing || this._loading ? "disabled" : ""}>＋ ${esc(this._t("importProject"))}</button>
                <button id="project-backups" ${project && !this._initializing && !this._loading ? "" : "disabled"}>↶ ${esc(this._t("backups"))}</button>
              </div>
            </div>
          </aside>

          <main class="content">
            ${this._progressMarkup()}
            ${this._loading && !this._previewLoading && !this._modeLoading && !this._installLoading ? (this._progress ? "" : `<div class="notice spinner">${esc(this._t("loading"))}</div>`) : ""}
            ${this._error ? `<div class="error">${esc(this._error)}</div>` : ""}
            <div class="notice">
              <strong>${esc(development ? this._t("developmentMode") : this._t("readOnly"))}</strong><br>
              ${esc(development ? this._t("writesOn") : this._t("writesOff"))}
            </div>
            ${(project?.restart_pending || this._installResult?.restart_required) ? `
              <div class="restart-required" role="alert" aria-live="assertive">
                <strong>⚠ ${esc(this._t("restartRequiredTitle"))}</strong>
                <div>${esc(this._t("restartRequiredBody"))}</div>
                <div class="restart-action">${esc(this._t("restartRequiredAction"))}</div>
              </div>
            ` : ""}
            ${currentFrontendReload ? `
              <div class="frontend-reload-required" role="status" aria-live="polite">
                <strong>↻ ${esc(this._t("frontendReloadTitle"))}</strong>
                <div>${esc(this._t("frontendReloadBody"))}</div>
                <button class="primary" id="frontend-reload">${esc(this._t("frontendReloadAction"))}</button>
              </div>
            ` : ""}
            ${this._installResult ? `
              <div class="success">
                <strong>${esc(this._t("installDone"))}</strong><br>
                ${esc(this._t("transaction"))}: <code>${esc(this._installResult.transaction_id)}</code><br>
                ${esc(this._t("backup"))}: <code>${esc(this._installResult.backup_path || "—")}</code><br>
                ${esc(this._installResult.restart_required ? this._t("restartRequired") : this._installResult.lifecycle === "frontend_reload" ? this._t("frontendReloadRequired") : this._t("noRestartRequired"))}
              </div>
            ` : ""}
            ${this._restoreResult ? `
              <div class="success">
                <strong>${esc(this._t("backupRestoreDone"))}</strong><br>
                ${esc(this._t("transaction"))}: <code>${esc(this._restoreResult.transaction_id)}</code><br>
                ${esc(this._t("backupRestoreSafety"))}: <code>${esc(this._restoreResult.safety_backup_path || "—")}</code><br>
                ${esc(this._restoreResult.restart_required ? this._t("restartRequired") : this._restoreResult.lifecycle === "frontend_reload" ? this._t("frontendReloadRequired") : this._t("noRestartRequired"))}
              </div>
            ` : ""}

            <section class="workflow-guide" aria-label="${esc(this._t("workflowTitle"))}">
              <h2>${esc(this._t("workflowTitle"))}</h2>
              <div class="workflow-hint">${esc(this._t("workflowHint"))}</div>
              <div class="workflow-steps">
                <button type="button" id="workflow-step-1" class="workflow-step ${recommendedSelected ? "done" : project ? "current" : ""}">1 · ${esc(this._t("workflowStep1"))}</button>
                <button type="button" id="workflow-step-2" class="workflow-step ${previewReady ? "done" : recommendedSelected ? "current" : ""}">2 · ${esc(this._t("workflowStep2"))}</button>
                <button type="button" id="workflow-step-3" class="workflow-step ${development ? "done" : previewReady && !noChanges ? "current" : ""}">3 · ${esc(this._t("workflowStep3"))}</button>
                <button type="button" id="workflow-step-4" class="workflow-step ${installDone ? "done" : development && previewReady && !noChanges ? "current" : ""}">4 · ${esc(this._t("workflowStep4"))}</button>
              </div>
              <div class="workflow-next">
                <span>${esc(nextStep)}</span>
                ${previewReady && !this._previewLoading ? `<span class="workflow-next-lifecycle">${esc(this._t("lifecycleTitle"))}: ${esc(previewLifecycleLabel)}</span>` : ""}
              </div>
            </section>

            ${project ? `
              <div class="grid">
                <section class="card">
                  <h2>${esc(project.title)}</h2>
                  ${project.restart_pending ? `
                    <div class="project-restart-pending">⚠ ${esc(this._t("restartPendingShort"))}</div>
                  ` : ""}
                  <div class="meta">
                    <div class="key">${esc(this._t("repo"))}</div>
                    <div class="value">${esc(project.repository)}</div>
                    <div class="key">${esc(this._t("manifest"))}</div>
                    <div class="value">${esc(project.manifest_path)}</div>
                    <div class="key">Status</div>
                    <div class="value">${esc(project.status || "—")}</div>
                    <div class="key">${esc(this._t("token"))}</div>
                    <div class="value">${esc(project.token_configured ? this._t("tokenOk") : this._t("tokenMissing"))}</div>
                  </div>
                  <div class="row" style="margin-top:14px">
                    <button id="project-config">${esc(this._t("config"))}</button>
                  </div>
                </section>

                <section class="card workflow-target" id="source-card">
                  <h2>${esc(this._t("source"))}</h2>

                  ${recommendation?.available ? `
                    <div class="recommendation ${recommendation.safe_selected ? "" : (recommendation.explicit_policy ? "warning" : "error")}">
                      <h3>${esc(this._t("recommendedDeployment"))}</h3>
                      <strong>${esc(
                        recommendation.status === "recommended_current"
                          ? this._t("recommendedCurrent")
                          : recommendation.status === "newer_recommended_available"
                            ? this._t("recommendedNewer")
                            : recommendation.status === "different_source_selected"
                              ? this._t("recommendedDifferent")
                              : recommendation.explicit_policy
                                ? this._t("recommendedAvailable")
                                : this._t("recommendedFallback")
                      )}</strong>
                      <div class="meta" style="margin-top:10px">
                        <div class="key">${esc(this._t("channel"))}</div>
                        <div class="value">${esc(recommendation.channel || "—")}</div>
                        <div class="key">Ref</div>
                        <div class="value">${esc(recommendation.ref || "—")}</div>
                        <div class="key">Commit</div>
                        <div class="value"><code>${esc(shortSha(recommendation.commit_sha))}</code></div>
                      </div>
                      <div class="row" style="margin-top:12px">
                        <button class="primary" id="use-recommended" ${recommendation.safe_selected ? "disabled" : ""}>
                          ${recommendation.safe_selected ? `✓ 1 · ${esc(this._t("workflowStep1"))}` : esc(this._t("useRecommended"))}
                        </button>
                      </div>
                    </div>
                  ` : `
                    <div class="recommendation error">
                      <h3>${esc(this._t("recommendedDeployment"))}</h3>
                      ${esc(this._t("recommendedUnavailable"))}
                    </div>
                  `}

                  <div class="meta">
                    <div class="key">Ausgewählt · Art</div>
                    <div class="value">${esc(project.selected_source_kind || "—")}</div>
                    <div class="key">Ausgewählt · Ref</div>
                    <div class="value">${esc(project.selected_source_ref || "—")}</div>
                    <div class="key">Ausgewählt · Commit</div>
                    <div class="value"><code>${esc(shortSha(project.selected_source_commit))}</code></div>
                  </div>

                  <details class="advanced" id="advanced-sources" ${this._advancedSourcesOpen ? "open" : ""}>
                    <summary>${esc(this._t("advancedSources"))}</summary>
                    <div class="footer-note">${esc(this._t("advancedWarning"))}</div>
                    <div class="row" style="margin-top:10px">
                      <select id="source-select">
                        ${(this._sources?.candidates || []).map((item) => {
                          const value = JSON.stringify({ kind: item.kind, ref: item.ref });
                          return `<option value='${esc(value)}' ${value === this._sourceChoice ? "selected" : ""}>${esc(item.label)}${item.commit_sha ? ` · ${esc(shortSha(item.commit_sha))}` : ""}</option>`;
                        }).join("")}
                        <option value="__manual__" ${this._sourceChoice === "__manual__" ? "selected" : ""}>${esc(this._t("manualCommit"))}</option>
                      </select>
                      <button class="${sourceSelectionPending ? "primary" : ""}" id="apply-source">${esc(this._t("applySource"))}</button>
                    </div>
                    <div class="notice source-selection-pending" style="margin-top:10px;margin-bottom:0;${sourceSelectionPending ? "" : "display:none"}">${esc(this._t("sourceSelectionPending"))}</div>
                    <div class="row" id="manual-row" style="margin-top:10px; ${this._sourceChoice === "__manual__" ? "" : "display:none"}">
                      <input id="manual-commit" type="text" placeholder="0123456789abcdef…" value="${esc(this._manualCommit)}">
                    </div>
                    ${this._sources?.truncated ? `<div class="footer-note">${esc(this._t("truncated"))}</div>` : ""}
                  </details>
                </section>
              </div>

              <section class="card preview-card workflow-target" id="preview-card" ${(this._previewLoading || this._installLoading) ? 'aria-busy="true"' : ""}>
                <h2 style="margin:0">${esc(this._t("preview"))}</h2>

                ${this._preview && !this._previewLoading ? `
                  <div class="preview-ready-hint" role="status" aria-live="polite">
                    <div>${esc(this._t("previewReadyHint"))}</div>
                    ${this._preview?.integrity?.checksums_complete ? `
                      <div class="preview-integrity">
                        <span>${esc(this._t("checksumValidDetail"))}</span>
                      </div>
                    ` : ""}
                  </div>

                  <div class="summary preview-summary" aria-label="${esc(this._t("preview"))}">
                    <div class="stat preview-stat add ${counts.add > 0 ? "active" : ""}">
                      <b>${counts.add}</b><span class="stat-label">${esc(this._t("add"))}</span>
                    </div>
                    <div class="stat preview-stat change ${counts.change > 0 ? "active" : ""}">
                      <b>${counts.change}</b><span class="stat-label">${esc(this._t("change"))}</span>
                    </div>
                    <div class="stat preview-stat remove ${counts.remove > 0 ? "active" : ""}">
                      <b>${counts.remove}</b><span class="stat-label">${esc(this._t("removed"))}</span>
                    </div>
                    <div class="stat preview-stat unchanged">
                      <b>${counts.unchanged}</b><span class="stat-label">${esc(this._t("unchanged"))}</span>
                    </div>
                  </div>

                  <div class="preview-lifecycle-banner">
                    <strong>${esc(this._t("lifecycleTitle"))}:</strong> ${esc(previewLifecycleLabel)}
                  </div>

                  ${versionGuard ? `
                    <div class="version-check ${versionGuard.regression ? "regression" : (versionGuard.warning ? "warning" : "")}">
                      <strong>${esc(this._t("versionCheck"))}</strong><br>
                      ${esc(
                        versionGuard.regression
                          ? this._t("regressionWarning")
                          : versionGuard.reason === "same_version_with_file_changes"
                            ? this._t("sameVersionWarning")
                            : versionGuard.reason === "no_common_version_marker_with_removals"
                              ? this._t("unknownVersionWarning")
                              : versionGuard.status === "upgrade"
                                ? this._t("upgradeDetected")
                                : versionGuard.status === "same"
                                  ? this._t("sameVersionDetected")
                                  : this._t("versionUnknown")
                      )}
                      <div class="version-meta">
                        <div class="key">${esc(this._t("gitVersion"))}</div>
                        <div>${esc(versionGuard.source_version || "—")}</div>
                        <div class="key">${esc(this._t("localVersion"))}</div>
                        <div>${esc(versionGuard.local_version || "—")}</div>
                        <div class="key">${esc(this._t("versionMarker"))}</div>
                        <div><code>${esc(versionGuard.marker || "—")}</code></div>
                      </div>
                    </div>
                  ` : ""}
                ` : ""}

                <div class="guided-actions">
                  <button class="${this._previewLoading ? "preview-loading" : this._preview ? "preview-ready" : "primary"}"
                          id="load-preview"
                          ${project.selected_source_commit && !this._previewLoading && !this._modeLoading && !this._installLoading ? "" : "disabled"}
                          ${this._preview && !this._previewLoading ? `title="${esc(this._t("previewReadyHint"))}"` : ""}>
                    ${this._previewLoading
                      ? `<span class="button-spinner" aria-hidden="true"></span>${esc(this._t("previewLoading"))}`
                      : this._preview
                        ? `<span>${esc(this._t("previewReady"))}</span>${this._preview?.integrity?.checksums_complete ? `<span class="preview-checksum">${esc(this._t("checksumValid"))}</span>` : ""}<span class="preview-lifecycle-compact">${esc(previewLifecycleCompact)}</span>`
                        : esc(this._t("loadPreview"))}
                  </button>
                  <button class="${this._modeLoading ? "mode-loading" : development ? "danger" : ""}" id="mode-toggle"
                          ${this._preview && affected > 0 && !this._previewLoading && !this._modeLoading && !this._installLoading ? "" : "disabled"}>
                    ${this._modeLoading
                      ? `<span class="button-spinner" aria-hidden="true"></span>${esc(development ? this._t("lockLoading") : this._t("unlockLoading"))}`
                      : esc(development ? this._t("lock") : this._t("unlock"))}
                  </button>
                  <button class="${this._installLoading ? "install-loading" : installReady ? "install-ready" : "danger"}" id="install-project"
                          ${installReady ? "" : "disabled"}>
                    ${this._installLoading
                      ? `<span class="button-spinner" aria-hidden="true"></span>${esc(this._t("installLoading"))}`
                      : esc(installLabel)}
                  </button>
                </div>
                ${this._modeLoading ? `
                  <div class="mode-progress"
                       role="progressbar"
                       aria-label="${esc(development ? this._t("lockLoading") : this._t("unlockLoading"))}"></div>
                  <div class="mode-working" role="status" aria-live="polite">
                    ${esc(this._t("modeWorking"))}
                  </div>
                ` : ""}
                ${this._installLoading ? `
                  <div class="install-progress"
                       role="progressbar"
                       aria-label="${esc(this._t("installLoading"))}"></div>
                  <div class="install-working" role="status" aria-live="polite">
                    ${esc(this._t("installWorking"))}
                  </div>
                ` : ""}
                ${this._previewLoading ? `
                  <div class="preview-progress"
                       role="progressbar"
                       aria-label="${esc(this._t("previewLoading"))}"></div>
                ` : ""}

                ${this._preview ? `
                  <div class="toolbar">
                    <input id="search" type="text" placeholder="${esc(this._t("search"))}" value="${esc(this._search)}">
                    ${["all","add","change","remove","unchanged"].map((filter) => `
                      <button class="filter ${this._filter === filter ? "active" : ""}" data-filter="${filter}">
                        ${esc(this._t(filter))}
                      </button>
                    `).join("")}
                  </div>

                  <div class="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>${esc(this._t("operation"))}</th>
                          <th>${esc(this._t("path"))}</th>
                          <th>${esc(this._t("size"))}</th>
                          <th>${esc(this._t("sourceHash"))}</th>
                          <th>${esc(this._t("targetHash"))}</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${this._filteredFiles().map((file) => `
                          <tr>
                            <td class="op ${esc(file.operation)}">${esc(this._operationLabel(file.operation))}</td>
                            <td class="path">${esc(file.target_path)}</td>
                            <td>${esc(formatBytes(file.source_size ?? file.target_size))}</td>
                            <td class="hash">${esc(shortSha(file.source_sha256))}</td>
                            <td class="hash">${esc(shortSha(file.target_sha256))}</td>
                          </tr>
                        `).join("")}
                      </tbody>
                    </table>
                  </div>
                  <div class="footer-note">${this._filteredFiles().length} ${esc(this._t("files"))}</div>
                ` : `<div class="empty">${esc(project.selected_source_commit ? this._t("noPreview") : this._t("noSource"))}</div>`}
              </section>
            ` : `<div class="empty">${esc(this._t("selectProject"))}</div>`}

            <deploy-relay-diagnostics-panel id="diagnostics-panel"></deploy-relay-diagnostics-panel>
          </main>
        </div>

        ${this._showImport ? `
          <div class="modal-backdrop" id="import-backdrop">
            <div class="modal" role="dialog" aria-modal="true">
              <h2>${esc(this._t("importTitle"))}</h2>
              <div class="field">
                <label for="import-repo">${esc(this._t("repository"))}</label>
                <input id="import-repo" type="text"
                       placeholder="TheDaimos/weather-router-dev"
                       value="${esc(this._importRepo)}">
              </div>
              <div class="field">
                <label for="import-manifest">${esc(this._t("manifestPath"))}</label>
                <input id="import-manifest" type="text"
                       value="${esc(this._importManifest)}">
              </div>
              <div class="field">
                <label for="import-token">${esc(this._t("githubToken"))}</label>
                <input id="import-token" type="password" autocomplete="off"
                       value="${esc(this._importToken)}">
                <small>${esc(this._t("tokenHint"))}</small>
              </div>
              <div class="modal-actions">
                <button id="import-cancel">${esc(this._t("cancel"))}</button>
                <button class="primary" id="import-submit">${esc(this._t("importNow"))}</button>
              </div>
            </div>
          </div>
        ` : ""}

        ${this._showRemove && project ? `
          <div class="modal-backdrop" id="remove-backdrop">
            <div class="modal" role="dialog" aria-modal="true" aria-labelledby="remove-title">
              <h2 id="remove-title">${esc(this._t("removeTitle"))}: ${esc(project.title)}</h2>
              <div class="modal-warning">
                <strong>${esc(project.repository)}</strong><br><br>
                ${esc(this._t("removeWarning"))}


              </div>
              <div class="field">
                <label for="remove-confirm">${esc(this._t("removeTypePrompt"))} <strong>${esc(project.title)}</strong></label>
                <input id="remove-confirm" type="text" autocomplete="off"
                       value="${esc(this._removeConfirmText)}"
                       placeholder="${esc(project.title)}">
              </div>
              <div class="modal-actions">
                <button id="remove-cancel">${esc(this._t("cancel"))}</button>
                <button class="danger" id="remove-submit" ${this._removeConfirmText === project.title ? "" : "disabled"}>
                  ${esc(this._t("removeConfirm"))}
                </button>
              </div>
            </div>
          </div>
        ` : ""}

        ${this._showBackups && project ? `
          <div class="modal-backdrop" id="backup-backdrop">
            <div class="modal wide" role="dialog" aria-modal="true" aria-labelledby="backup-title">
              <button class="modal-close" id="backup-x" aria-label="${esc(this._t("backupClose"))}" title="${esc(this._t("backupClose"))}" ${this._restoreLoading ? "disabled" : ""}>×</button>
              <h2 id="backup-title">${esc(this._t("backupTitle"))}: ${esc(project.title)}</h2>
              <div class="batch-note">${esc(this._t("backupIntro"))}</div>

              <div class="backup-retention-row">
                <div class="field" style="margin:0">
                  <label for="backup-retention">${esc(this._t("backupRetention"))}</label>
                  <input id="backup-retention" type="number"
                         min="${esc(this._backupLimits.minimum)}"
                         max="${esc(this._backupLimits.maximum)}"
                         value="${esc(this._backupRetention)}"
                         ${this._backupLoading || this._restoreLoading ? "disabled" : ""}>
                  <small>${esc(this._t("backupRetentionHint"))}</small>
                </div>
                <button id="backup-retention-save" ${this._backupLoading || this._restoreLoading ? "disabled" : ""}>${esc(this._t("backupRetentionSave"))}</button>
              </div>

              ${this._backupMessage ? `<div class="batch-message">${esc(this._backupMessage)}</div>` : ""}
              ${this._restoreLoading ? this._progressMarkup() : ""}
              ${this._backupLoading ? `<div class="notice spinner">${esc(this._t("loading"))}</div>` : ""}

              <div class="backup-list">
                ${!this._backupLoading && !this._backups.length ? `<div class="empty">${esc(this._t("backupEmpty"))}</div>` : ""}
                ${this._backups.map((item) => {
                  const kind = item.kind === "restore_safety"
                    ? this._t("backupKindRestoreSafety")
                    : this._t("backupKindDeployment");
                  const created = item.created_at ? new Date(item.created_at).toLocaleString() : "—";
                  return `
                    <div class="backup-item">
                      <div class="backup-main">
                        <span class="backup-kind">${esc(kind)} · ${esc(created)}</span>
                        <small>${esc(item.transaction_id)}</small>
                        <small>${esc(this._t("backupFiles"))}: ${esc(item.entries)} · ${esc(this._t("backupStored"))}: ${esc(item.stored_files)} · ${esc(formatBytes(item.total_bytes))}</small>
                        ${item.previous_version ? `<small>${esc(this._t("backupSavedVersion"))}: ${esc(item.previous_version)}</small>` : ""}
                        ${item.target_version ? `<small>${esc(this._t("backupTargetVersion"))}: ${esc(item.target_version)}</small>` : ""}
                        ${item.source_commit ? `<small>${esc(this._t("backupTargetVersion"))}: ${esc(shortSha(item.source_commit))}${item.source_ref ? ` · ${esc(item.source_ref)}` : ""}</small>` : ""}
                      </div>
                      <button class="danger" data-restore-backup="${esc(item.transaction_id)}"
                              ${this._restoreLoading || !item.restore_capable ? "disabled" : ""}
                              ${!item.restore_capable ? `title="${esc(this._t("backupLegacy"))}"` : ""}>
                        ${item.restore_capable
                          ? (this._restoreLoading ? esc(this._t("backupRestoreRunning")) : esc(this._t("backupRestore")))
                          : esc(this._t("backupLegacy"))}
                      </button>
                    </div>
                  `;
                }).join("")}
              </div>

              <div class="modal-actions">
                <button id="backup-close" ${this._restoreLoading ? "disabled" : ""}>${esc(this._t("backupClose"))}</button>
              </div>
            </div>
          </div>
        ` : ""}

        ${this._showBatch ? `
          <div class="modal-backdrop" id="batch-backdrop">
            <div class="modal wide" role="dialog" aria-modal="true" aria-labelledby="batch-title">
              <button class="modal-close" id="batch-x" aria-label="${esc(this._t("batchClose"))}" title="${esc(this._t("batchClose"))}" ${this._batchRunning ? "disabled" : ""}>×</button>
              <h2 id="batch-title">${esc(this._t("batchTitle"))}</h2>
              <div class="batch-note">${esc(this._t("batchIntro"))}</div>
              ${restartPending ? `<div class="notice">${esc(this._t("batchPendingRestart"))}</div>` : ""}
              <div class="batch-note">${esc(this._t("batchSelfLast"))}</div>
              <div class="batch-list">
                ${(this._state?.projects || []).map((item) => {
                  const batch = this._batchItems[item.subentry_id] || { status: "pending" };
                  const previewCounts = batch.preview?.counts || {};
                  const affectedCount = Number(previewCounts.add || 0) + Number(previewCounts.change || 0) + Number(previewCounts.remove || 0);
                  return `
                    <label class="batch-item">
                      <input type="checkbox" data-batch-project="${esc(item.subentry_id)}" ${this._batchSelected.has(item.subentry_id) ? "checked" : ""} ${this._batchRunning ? "disabled" : ""}>
                      <span class="batch-item-main">
                        <strong>${esc(item.title)}${item.restart_pending ? " · ⚠ Neustart" : ""}</strong>
                        <small>${esc(item.repository)}</small>
                        ${batch.preview ? `<small>${esc(shortSha(batch.preview?.recommendation?.commit_sha))} · ${affectedCount} Änderung(en)</small>` : ""}
                        ${batch.detail ? `<div class="batch-detail">${esc(batch.detail)}</div>` : ""}
                      </span>
                      <span class="batch-status ${esc(batch.status)}">${esc(this._batchStatusLabel(batch.status))}</span>
                    </label>
                  `;
                }).join("")}
              </div>
              ${this._batchMessage ? `<div class="batch-message">${esc(this._batchMessage)}</div>` : ""}
              ${this._batchRunning ? this._progressMarkup() : ""}
              <div class="modal-actions batch-actions">
                ${this._batchInstallComplete && batchNeedsFrontendReload ? `<button class="primary" id="batch-reload">${esc(this._t("frontendReloadAction"))}</button>` : ""}
                <button id="batch-close" ${this._batchRunning ? "disabled" : ""}>${esc(this._batchInstallComplete ? this._t("batchClose") : this._t("cancel"))}</button>
                <button class="${batchCheckRunning ? "batch-action-running" : this._batchCheckComplete ? "batch-action-success" : "primary"}" id="batch-check" ${this._batchRunning || batchSelectedCount === 0 || this._batchCheckComplete ? "disabled" : ""}>
                  ${batchCheckRunning ? `<span class="button-spinner" aria-hidden="true"></span>${esc(batchCheckLabel)}` : esc(batchCheckLabel)}
                </button>
                <button class="${this._batchPhase === "unlocking" ? "mode-loading" : development ? "batch-action-success" : ""}" id="batch-unlock" ${this._batchRunning || !this._batchCheckComplete || batchReadyCount === 0 || batchHasBlockers || development || this._batchInstallComplete ? "disabled" : ""}>
                  ${this._batchPhase === "unlocking"
                    ? `<span class="button-spinner" aria-hidden="true"></span>${esc(this._t("batchUnlockRunning"))}`
                    : esc(development ? this._t("batchUnlockDone") : this._t("batchUnlock"))}
                </button>
                <button class="${batchInstallRunning ? "batch-action-running" : this._batchInstallComplete ? "batch-action-success" : batchInstallReady ? "install-ready" : "danger"}" id="batch-install" ${batchInstallReady ? "" : "disabled"}>
                  ${batchInstallRunning ? `<span class="button-spinner" aria-hidden="true"></span>${esc(batchInstallLabel)}` : esc(batchInstallLabel)}
                </button>
              </div>
            </div>
          </div>
        ` : ""}
      </div>
    `;

    if (preservedDiagnosticsPanel) {
      const diagnosticsPlaceholder =
        this.shadowRoot.querySelector("#diagnostics-panel");
      if (
        diagnosticsPlaceholder
        && diagnosticsPlaceholder !== preservedDiagnosticsPanel
      ) {
        diagnosticsPlaceholder.replaceWith(preservedDiagnosticsPanel);
      }
    }

    this._bind();
  }

  _bind() {
    const diagnosticsPanel = this.shadowRoot.querySelector("#diagnostics-panel");
    if (diagnosticsPanel) {
      // Set the project first. The hass setter starts the first diagnostics
      // load, so this ordering avoids an unnecessary unscoped request followed
      // immediately by a second project-scoped request.
      diagnosticsPanel.project = this._project();
      diagnosticsPanel.hass = this.hass;
    }

    this.shadowRoot.querySelector("#refresh")?.addEventListener("click", () => this._loadState());
    this.shadowRoot.querySelector("#workflow-step-1")?.addEventListener("click", () => this._handleWorkflowStep(1));
    this.shadowRoot.querySelector("#workflow-step-2")?.addEventListener("click", () => this._handleWorkflowStep(2));
    this.shadowRoot.querySelector("#workflow-step-3")?.addEventListener("click", () => this._handleWorkflowStep(3));
    this.shadowRoot.querySelector("#workflow-step-4")?.addEventListener("click", () => this._handleWorkflowStep(4));
    this.shadowRoot.querySelector("#mode-toggle")?.addEventListener("click", () =>
      this._setMode(
        this._state?.deployment_mode === "development" ? "locked" : "development"
      )
    );
    this.shadowRoot.querySelector("#import-project")?.addEventListener("click", () => {
      this._showImport = true;
      this._render();
    });
    this.shadowRoot.querySelector("#project-backups")?.addEventListener("click", () => this._openBackups());
    this.shadowRoot.querySelector("#remove-project")?.addEventListener("click", () => {
      if (!this._project()) return;
      this._removeConfirmText = "";
      this._showRemove = true;
      this._render();
    });
    this.shadowRoot.querySelector("#project-config")?.addEventListener("click", () =>
      this._navigate("/config/integrations/integration/deploy_relay")
    );

    this.shadowRoot.querySelector("#import-cancel")?.addEventListener("click", () => {
      this._showImport = false;
      this._importToken = "";
      this._render();
    });
    this.shadowRoot.querySelector("#import-submit")?.addEventListener("click", () =>
      this._importProject()
    );
    this.shadowRoot.querySelector("#import-repo")?.addEventListener("input", (event) => {
      this._importRepo = event.target.value;
    });
    this.shadowRoot.querySelector("#import-manifest")?.addEventListener("input", (event) => {
      this._importManifest = event.target.value;
    });
    this.shadowRoot.querySelector("#import-token")?.addEventListener("input", (event) => {
      this._importToken = event.target.value;
    });

    this.shadowRoot.querySelector("#remove-cancel")?.addEventListener("click", () => {
      this._showRemove = false;
      this._removeConfirmText = "";
      this._render();
    });
    this.shadowRoot.querySelector("#remove-confirm")?.addEventListener("input", (event) => {
      this._removeConfirmText = event.target.value;
      const submit = this.shadowRoot.querySelector("#remove-submit");
      if (submit) submit.disabled = this._removeConfirmText !== this._project()?.title;
    });
    this.shadowRoot.querySelector("#remove-submit")?.addEventListener("click", () => this._removeProject());

    const closeBackupDialog = () => {
      if (this._restoreLoading) return;
      this._showBackups = false;
      this._backupMessage = "";
      this._render();
    };
    this.shadowRoot.querySelector("#backup-close")?.addEventListener("click", closeBackupDialog);
    this.shadowRoot.querySelector("#backup-x")?.addEventListener("click", closeBackupDialog);
    this.shadowRoot.querySelector("#backup-retention")?.addEventListener("input", (event) => {
      this._backupRetention = Number(event.target.value);
    });
    this.shadowRoot.querySelector("#backup-retention-save")?.addEventListener("click", () => this._saveBackupRetention());
    this.shadowRoot.querySelectorAll("[data-restore-backup]").forEach((button) => {
      button.addEventListener("click", () => this._restoreBackup(button.dataset.restoreBackup));
    });

    const closeBatchDialog = () => {
      if (this._batchRunning) return;
      this._showBatch = false;
      this._batchRunning = false;
      this._batchPhase = "idle";
      this._batchMessage = "";
      this._render();
    };
    this.shadowRoot.querySelector("#batch-close")?.addEventListener("click", closeBatchDialog);
    this.shadowRoot.querySelector("#batch-x")?.addEventListener("click", closeBatchDialog);
    this.shadowRoot.querySelectorAll("[data-batch-project]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) this._batchSelected.add(checkbox.dataset.batchProject);
        else this._batchSelected.delete(checkbox.dataset.batchProject);
        this._batchCheckComplete = false;
        this._batchInstallComplete = false;
        this._batchInstallFailed = false;
        this._batchMessage = "";
        this._render();
      });
    });
    this.shadowRoot.querySelector("#batch-check")?.addEventListener("click", () => this._batchPreviewSelected());
    this.shadowRoot.querySelector("#batch-unlock")?.addEventListener("click", () => this._batchEnableWrites());
    this.shadowRoot.querySelector("#batch-install")?.addEventListener("click", () => this._batchInstallSelected());
    this.shadowRoot.querySelector("#batch-reload")?.addEventListener("click", () => window.location.reload());
    this.shadowRoot.querySelector("#frontend-reload")?.addEventListener("click", () => window.location.reload());

    this.shadowRoot.querySelector("#project-select")?.addEventListener("change", async (event) => {
      if (this._initializing || this._loading) return;
      if (event.target.value === "__batch_update__") {
        this._openBatch();
        return;
      }
      this._selectedProjectId = event.target.value || null;
      this._sources = null;
      this._preview = null;
      this._installResult = null;
      this._restoreResult = null;
      this._showBackups = false;
      this._advancedSourcesOpen = false;
      this._filter = "all";
      this._search = "";
      this._render();
      if (this._selectedProjectId) await this._loadSources();
    });

    this.shadowRoot.querySelector("#advanced-sources")?.addEventListener("toggle", (event) => {
      this._advancedSourcesOpen = Boolean(event.target.open);
    });
    this.shadowRoot.querySelector("#source-select")?.addEventListener("change", (event) => {
      this._sourceChoice = event.target.value;
      this._syncAdvancedSourceControls();
    });
    this.shadowRoot.querySelector("#manual-commit")?.addEventListener("input", (event) => {
      this._manualCommit = event.target.value;
      this._syncAdvancedSourceControls();
    });
    this.shadowRoot.querySelector("#use-recommended")?.addEventListener("click", () => this._useRecommended());
    this.shadowRoot.querySelector("#apply-source")?.addEventListener("click", () => this._selectSource());
    this.shadowRoot.querySelector("#load-preview")?.addEventListener("click", () => this._loadPreview());
    this.shadowRoot.querySelector("#install-project")?.addEventListener("click", () => this._install());

    this.shadowRoot.querySelector("#search")?.addEventListener("input", (event) => {
      this._search = event.target.value;
      this._render();
    });
    this.shadowRoot.querySelectorAll("[data-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        this._filter = button.dataset.filter;
        this._render();
      });
    });
  }
}

if (!customElements.get("deploy-relay-panel")) {
  customElements.define("deploy-relay-panel", DeployRelayPanel);
}
