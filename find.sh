grep -Eri '([^[:alnum:]\-]|^)'$1'([^[:alnum:]\-]|$)' \etnc19_web_2019_100000 --color=always | grep -v "<doc" --color=always | less -R
