# vpn 快速啟動

```sh
#!/bin/bash
vpn_pid=$(ps aux | grep openfortivpn | awk '{print $2}' | wc -l)

if [ $vpn_pid -gt 1 ]; then
  status="connected"
else
  status="disconnected"
fi

echo '<?xml version="1.0"?>
<items>
  <item uid="vpn" valid="yes" autocomplete="vpn">
    <title>Status: '"$status"'</title>
    <subtitle>dottomesh</subtitle>
  </item>
</items>'
```
