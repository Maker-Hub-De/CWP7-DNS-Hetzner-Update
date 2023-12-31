<?php

if ( !isset( $include_path ) )
{
    echo "invalid access";
    exit( );
}

$strConfig = shell_exec('/usr/local/bin/hetznerdns/configGet.py');
$objConfig = json_decode($strConfig);

/*$objFileHandler = fopen('/usr/local/bin/hetznerdns/config.json', 'r');

if ($objFileHandler !== false) {
  $strConfig = fread($objFileHandler, filesize('/usr/local/bin/hetznerdns/config.json'));
  $objConfig = json_decode($strConfig);
  fclose($objFileHandler); // Wichtig: Die Datei nach dem Lesen schließen
}*/
?>

Hetzner DNS Zone update<br>
<form class="form-horizontal group-border stripped" action="" method="post">
  <div class="form-group">
    <label class="col-lg-2 col-md-3 control-label" for="">Aktive:</label>
      <div class="col-lg-10 col-md-9">
        <div class="toggle-custom toggle-inline">
          <label class="toggle tip" data-original-title="Status" data-on="ON" data-off="OFF">
            <input type="checkbox" class="" id="checkbox-toggle" <?php if (isset($objConfig) && property_exists($objConfig, 'active') && $objConfig->active == true) echo 'checked'; ?> name="checkbox-toggle">
            <span class="button-checkbox"></span>
          </label>
        </div>
      </div>
  </div>
  <div class="form-group">
    <label class="col-lg-2 col-md-3 control-label" for="">API-Token:</label>
      <div class="col-lg-10 col-md-9">
        <input type="text" class="form-control formadd" name="apiToken" id="apiToken" maxlength="32" value="<?php if (isset($objConfig) && property_exists($objConfig, 'apiToken')) echo $objConfig->apiToken; ?>">
        <span class="help-block">Enter Hetzer DNS API access tokens</span>
    </div>
    <label class="col-lg-2 col-md-3 control-label" for="">Directory:</label>
      <div class="col-lg-10 col-md-9">
        <input type="text" class="form-control formadd" name="directory" id="directory" maxlength="255" value="<?php if (isset($objConfig) && property_exists($objConfig, 'directory')) echo $objConfig->directory; else echo '/var/named' ?>">
        <span class="help-block">The directory that should be monitored for changes (default is '/var/named').</span>
    </div>
  </div>    
</form>
