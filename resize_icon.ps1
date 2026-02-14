Add-Type -AssemblyName System.Drawing
$path = "\\192.168.7.222\config\custom_components\maya_knox\icon.png"
$img = [System.Drawing.Image]::FromFile($path)
Write-Host "SIZE: $($img.Width)x$($img.Height)"
if ($img.Width -gt 512) {
    $newImg = new-object System.Drawing.Bitmap(512, 512)
    $graph = [System.Drawing.Graphics]::FromImage($newImg)
    $graph.DrawImage($img, 0, 0, 512, 512)
    $newImg.Save("\\192.168.7.222\config\custom_components\maya_knox\icon_resized.png", [System.Drawing.Imaging.ImageFormat]::Png)
    $newImg.Dispose()
    $graph.Dispose()
    Write-Host "RESIZED"
}
else {
    Write-Host "OK"
}
$img.Dispose()
