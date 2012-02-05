MathJax.Hub.Config({
  showProcessingMessages: false,
  messageStyle: "none",
  "HTML-CSS": {
    availableFonts: ["TeX"], 
  },
});

MathJax.Hub.Queue(function () {
if (document.location.hash) {setTimeout("document.location = document.location.hash",1)} 
});

MathJax.Ajax.loadComplete("http://www.xmds.org/_static/mathjax-use-tex-fonts.js");
