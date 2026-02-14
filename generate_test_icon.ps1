Add-Type -AssemblyName System.Drawing
$img = new-object System.Drawing.Bitmap(256, 256)
$graph = [System.Drawing.Graphics]::FromImage($img)
$brush = [System.Drawing.Brushes]::Red
$graph.FillRectangle($brush, 0, 0, 256, 256)
$img.Save("\\192.168.7.222\config\custom_components\maya_knox\icon_test.png", [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()
$graph.Dispose()
