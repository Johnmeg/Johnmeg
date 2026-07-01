<#
.SYNOPSIS
    Registers the SAP Analytics Cloud tenant https://fanalca-clpriv-sac.us21.analytics.cloud.sap
    as an allowed AppDomain for the SAP Analytics Cloud, Digital Boardroom Excel add-in.

.DESCRIPTION
    Must be run as a Microsoft 365 administrator from a Windows machine with the
    O365CentralizedAddInDeployment PowerShell module installed. See
    sap-analytics-tenant-config.md for the full procedure.

.NOTES
    Run Connect-OrganizationAddInService interactively before this script;
    it opens a login dialog and cannot be scripted non-interactively.
#>

$ProductId = "8a512e2b-c04e-4c06-9235-11b6cd59f584"
$AppDomains = @(
    "https://hcs.cloud.sap",
    "https://fanalca-clpriv-sac.us21.analytics.cloud.sap"
)

Connect-OrganizationAddInService

Set-OrganizationAddInOverrides -ProductId $ProductId -AppDomains $AppDomains
