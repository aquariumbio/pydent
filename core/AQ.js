aq = require('./utils.js').aq;
var extend = require('util')._extend
var request = require('request')

AQ = global.AQ;

module.exports = {};

AQ.init = function(http) {
  AQ.next_record_id = 0;
}

AQ.get = function(path) {

  var headers;

  if ( AQ.login_headers ) {
    headers = {
      cookie: AQ.login_headers["set-cookie"]
    }
  } else {
    headers = {};
  }

  return new Promise(function(resolve,reject) {
    request.get({
        url: AQ.config.aquarium_url + path,
        headers: headers },
      function (error, response, body) {
        if (!error && response.statusCode == 200) {
          resolve({data: body});
        } else {
          // console.log([error,response,body])
          reject({error: error, statusCode: response.statusCode, body: body});
        }
      })
  });
}

AQ.post = function(path,data) {

  var headers;

  var c = AQ.login_headers["set-cookie"];
  c.push(c[0].replace('remember_token_development', 'remember_token'));

  if ( AQ.login_headers ) {
    headers = {
      cookie: c
    }
  } else {
    headers = {};
  }

  return new Promise(function(resolve,reject) {
    request({
        method: 'post',
        url: AQ.config.aquarium_url + path,
        headers: headers,
        form: extend(data, { authentication_key: AQ.authkey }) },
      function (error, response, body) {
        var parsed_body;
        try {
          parsed_body = JSON.parse(body)
        } catch(e) {
          parsed_body = null;
        }
        if (!error && parsed_body && response.statusCode == 200) {
          resolve({ data: parsed_body});
        } else {
          reject({error: error, statusCode: response.statusCode, body: body});
        }
      })
  });

}

AQ.get_sample_names = function() {

  return new Promise(function(resolve,reject) {
    AQ.get('/browser/all').then(
      (response) => {
        AQ.sample_names = response.data;
        resolve(AQ.sample_names);
      }, (response) => {
        reject(response.data.errors);
      }
    );
  });

}

AQ.sample_names_for = function(sample_type_name) {

  var samples = [];
  if ( sample_type_name ) {
    aq.each([sample_type_name],function(type) {
      samples = samples.concat(AQ.sample_names[type])
    });
  }
  return samples;

}

AQ.id_from = function(sid) {
  return sid.split(":")[0];
}

AQ.sid_from = function(id) {

}

AQ.items_for = function(sample_id,object_type_id) {

  return new Promise(function(resolve,reject) {

    AQ.post('/json/items/', { sid: sample_id, oid: object_type_id }) .then(
      (response) => {
        resolve(aq.collect(response.data, (item) => {
          if ( item.collection ) {
            var i = item;
            i.collection = AQ.Collection.record(i.collection);
            return new AQ.Record(AQ.Item,item);
          } else {
            return new AQ.Record(AQ.Item,item);
          }
        }));
      }, (response) => {
        reject(response.data.errors);
      }
    );

  });

}
