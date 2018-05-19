
import {zip} from './func';


if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}


if (!Object.values) {
    Object.values = data => Object.keys(data).map(k => data[k]);
}


if (Object.fromIterable)
    throw new Error('Object.fromIterable is already defined');

Object.fromIterable = function (it) {
    const rv = {};
    for (let [key, value] of it)
        rv[key] = value;
    return rv;
}


if (Object.fromKeysValues)
    throw new Error('Object.fromKeysValues is already defined');

Object.fromKeysValues = function (keysIt, valuesIt) {
    return Object.fromIterable(zip([keysIt, valuesIt]));
}
