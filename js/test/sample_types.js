require("../trident.js");

AQ.login_interactive().then(response => {

  AQ.SampleType.all().then(sts => {
    aq.each(sts, st => console.log("" + st.id + ": " + st.name))
  })

})
