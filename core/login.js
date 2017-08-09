var readline = require('readline');
var request = require('request')

AQ.login = function(username, password) {

  return new Promise(function(resolve,reject) {
    request.post(AQ.config.aquarium_url+"/sessions.json", { json: { session: { login: username, password: password } } },
      function (error, response, body) {
        if (!error && response.statusCode == 200) {
          AQ.login_headers = response.headers;
          console.log("LOGIN OK")
          resolve(body);
        } else {
          reject({error: error, statusCode: response.statusCode, body: body});
        }
      })
  });

}

AQ.login_interactive = function() {

  var rl = readline.createInterface(process.stdin, process.stdout);

  function hidden(query, callback) {

    var stdin = process.openStdin(),
        i = 0;

    process.stdin.on("data", function(char) {
        char = char + "";
        switch (char) {
            case "\n":
            case "\r":
            case "\u0004":
                stdin.pause();
                break;
            default:
                process.stdout.write("\033[2K\033[200D" + query + Array(rl.line.length+1).join("*"));
                i++;
                break;
        }
    });

    rl.question(query, function(value) {
        rl.history = rl.history.slice(1);
        callback(value);
    });

  }

  return new Promise(function(resolve, reject) {

    rl.question("username> ", username => {
      hidden('password> ', password => {
        rl.close();
        AQ.login(username,password).then(resolve).catch(reject);
      })
    })

  })

}
