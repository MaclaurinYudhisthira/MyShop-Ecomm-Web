ele=document.getElementsByClassName('flash')[0]
if (ele)
    window.onload=setTimeout(function(){console.log(ele.style.display='None')},3000);
