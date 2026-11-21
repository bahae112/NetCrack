# 🛡️ WiFi Pentest Toolkit

Outil de pentest Wi-Fi en Python (WEP, WPA/WPA2-PSK, AirSnitch) avec interface graphique, laboratoires de test reproductibles et support Docker.

---

## 📁 Structure du projet

```
wifi-pentest-toolkit/
│
├── app/                             
│   ├── main.py                    
│   ├── ui.py                        
│   ├── config.py                    
│   │
│   ├── attacks/                   
│   │   ├── wep_cracker.py          
│   │   ├── wpa_cracker.py          
│   │   └── airsnitch_attack.py      
│
├── labs/                          
│   ├── wep_lab/                 
│   │   └── hostapd_wep.conf       
│   │
│   ├── wpa_lab/                     
│   │   ├── hostapd_wpa.conf         
│   │   └── hostapd_wpa2.conf        
│   │
│   └── airsnitch_lab/              
│       └── hostapd_airsnitch.conf   
│
├── scripts/
│   ├── lab_wep_up.sh           
│   ├── lab_wpa_up.sh               
│   ├── lab_airsnitch_up.sh         
│   └── cleanup.sh
│
├── Dockerfile
├── .gitignore
├── README.md
└── requirements.txt
```

---

