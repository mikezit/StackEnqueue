$(function(){$(".string_list_widget_button").live("click",function(){$but=$(this);if($but.is(".add")){$new=$('<div style="display: none;"><input style="width: 600px;" type="text" name="'+$but.attr("name")+'" value="" /><button class="string_list_widget_button">-</button></div>');$but.before($new);$new.slideDown("fast")}else{$but.parent().slideUp("fast",function(){$but.parent().remove()})}return false});$(".fieldtool").each(function(){var a=$(this);var c=a.parent().parent().find("input, textarea");var b=c.attr("name");if(a.is(".context")){a.click(function(){var d=$('<input type="text" value="'+b+'" />');a.replaceWith(d)})}else{if(a.is(".default")){if(c.length==1&&(c.is("[type=text]")||c.is("textarea"))){a.click(function(){$.post(b+"/",function(d){c.val(d)})})}else{a.attr("href",b+"/")}}}});$(".url_field").each(function(){var d=$(this);var b=d.parent().find(".url_field_anchor");var a=b.attr("href");function c(){var e=a+"/"+d.val();b.attr("href",e);b.html(e)}d.keyup(c);c()});$("#test_email_settings a.test_button").click(function(){$("div.test_status").hide("slow");$("div.ajax_indicator").show("fast");$.post($(this).attr("href"),function(a){$("div.ajax_indicator").hide("fast");$("div.test_status").html(a);$("div.test_status").show("slow")})})});(function(b){b.fn.extend({autocomplete:function(a,f){var e=typeof a=="string";f=b.extend({},b.Autocompleter.defaults,{url:e?a:null,data:e?null:a,delay:e?b.Autocompleter.defaults.delay:10,max:f&&!f.scroll?10:150},f);f.highlight=f.highlight||function(c){return c};f.formatMatch=f.formatMatch||f.formatItem;return this.each(function(){new b.Autocompleter(this,f)})},result:function(a){return this.bind("result",a)},search:function(a){return this.trigger("search",[a])},flushCache:function(){return this.trigger("flushCache")},setOptions:function(a){return this.trigger("setOptions",[a])},unautocomplete:function(){return this.trigger("unautocomplete")}});b.Autocompleter=function(J,O){var S={UP:38,DOWN:40,DEL:46,TAB:9,RETURN:13,ESC:27,COMMA:188,PAGEUP:33,PAGEDOWN:34,BACKSPACE:8};var T=b(J).attr("autocomplete","off").addClass(O.inputClass);var L;var F="";var I=b.Autocompleter.Cache(O);var Q=0;var A;var a={mouseDownOnSelect:false};var D=b.Autocompleter.Select(O,J,R,a);var y;b.browser.opera&&b(J.form).bind("submit.autocomplete",function(){if(y){y=false;return false}});T.bind((b.browser.opera?"keypress":"keydown")+".autocomplete",function(c){A=c.keyCode;switch(c.keyCode){case S.UP:c.preventDefault();if(D.visible()){D.prev()}else{B(0,true)}break;case S.DOWN:c.preventDefault();if(D.visible()){D.next()}else{B(0,true)}break;case S.PAGEUP:c.preventDefault();if(D.visible()){D.pageUp()}else{B(0,true)}break;case S.PAGEDOWN:c.preventDefault();if(D.visible()){D.pageDown()}else{B(0,true)}break;case O.multiple&&b.trim(O.multipleSeparator)==","&&S.COMMA:case S.TAB:case S.RETURN:if(R()){c.preventDefault();y=true;return false}break;case S.ESC:D.hide();break;default:clearTimeout(L);L=setTimeout(B,O.delay);break}}).focus(function(){Q++}).blur(function(){Q=0;if(!a.mouseDownOnSelect){C()}}).click(function(){if(Q++>1&&!D.visible()){B(0,true)}}).bind("search",function(){var d=(arguments.length>1)?arguments[1]:null;function c(f,g){var e;if(g&&g.length){for(var h=0;h<g.length;h++){if(g[h].result.toLowerCase()==f.toLowerCase()){e=g[h];break}}}if(typeof d=="function"){d(e)}else{T.trigger("result",e&&[e.data,e.value])}}b.each(N(T.val()),function(e,f){P(f,c,c)})}).bind("flushCache",function(){I.flush()}).bind("setOptions",function(){b.extend(O,arguments[1]);if("data" in arguments[1]){I.populate()}}).bind("unautocomplete",function(){D.unbind();T.unbind();b(J.form).unbind(".autocomplete")});function R(){var d=D.selected();if(!d){return false}var e=d.result;F=e;if(O.multiple){var c=N(T.val());if(c.length>1){e=c.slice(0,c.length-1).join(O.multipleSeparator)+O.multipleSeparator+e}e+=O.multipleSeparator}T.val(e);z();T.trigger("result",[d.data,d.value]);return true}function B(c,d){if(A==S.DEL){D.hide();return}var e=T.val();if(!d&&e==F){return}F=e;e=M(e);if(e.length>=O.minChars){T.addClass(O.loadingClass);if(!O.matchCase){e=e.toLowerCase()}P(e,K,z)}else{H();D.hide()}}function N(d){if(!d){return[""]}var c=d.split(O.multipleSeparator);var e=[];b.each(c,function(g,f){if(b.trim(f)){e[g]=b.trim(f)}});return e}function M(d){if(!O.multiple){return d}var c=N(d);return c[c.length-1]}function E(d,c){if(O.autoFill&&(M(T.val()).toLowerCase()==d.toLowerCase())&&A!=S.BACKSPACE){T.val(T.val()+c.substring(M(F).length));b.Autocompleter.Selection(J,F.length,F.length+c.length)}}function C(){clearTimeout(L);L=setTimeout(z,200)}function z(){var c=D.visible();D.hide();clearTimeout(L);H();if(O.mustMatch){T.search(function(e){if(!e){if(O.multiple){var d=N(T.val()).slice(0,-1);T.val(d.join(O.multipleSeparator)+(d.length?O.multipleSeparator:""))}else{T.val("")}}})}if(c){b.Autocompleter.Selection(J,J.value.length,J.value.length)}}function K(c,d){if(d&&d.length&&Q){H();D.display(d,c);E(c,d[0].value);D.show()}else{z()}}function P(e,g,f){if(!O.matchCase){e=e.toLowerCase()}var c=I.load(e);if(c&&c.length){g(e,c)}else{if((typeof O.url=="string")&&(O.url.length>0)){var d={timestamp:+new Date()};b.each(O.extraParams,function(i,h){d[i]=typeof h=="function"?h():h});b.ajax({mode:"abort",port:"autocomplete"+J.name,dataType:O.dataType,url:O.url,data:b.extend({q:M(e),limit:O.max},d),success:function(h){var i=O.parse&&O.parse(h)||G(h);I.add(e,i);g(e,i)}})}else{D.emptyList();f(e)}}}function G(g){var f=[];var c=g.split("\n");for(var e=0;e<c.length;e++){var d=b.trim(c[e]);if(d){d=d.split("|");f[f.length]={data:d,value:d[0],result:O.formatResult&&O.formatResult(d,d[0])||d[0]}}}return f}function H(){T.removeClass(O.loadingClass)}};b.Autocompleter.defaults={inputClass:"ac_input",resultsClass:"ac_results",loadingClass:"ac_loading",minChars:1,delay:400,matchCase:false,matchSubset:true,matchContains:false,cacheLength:10,max:100,mustMatch:false,extraParams:{},selectFirst:true,formatItem:function(a){return a[0]},formatMatch:null,autoFill:false,width:0,multiple:false,multipleSeparator:", ",highlight:function(d,a){return d.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)("+a.replace(/([\^\$\(\)\[\]\{\}\*\.\+\?\|\\])/gi,"\\$1")+")(?![^<>]*>)(?![^&;]+;)","gi"),"<strong>$1</strong>")},scroll:true,scrollHeight:180};b.Autocompleter.Cache=function(n){var k={};var m=0;function i(c,d){if(!n.matchCase){c=c.toLowerCase()}var e=c.indexOf(d);if(e==-1){return false}return e==0||n.matchContains}function j(c,d){if(m>n.cacheLength){a()}if(!k[c]){m++}k[c]=d}function l(){if(!n.data){return false}var e={},f=0;if(!n.url){n.cacheLength=1}e[""]=[];for(var c=0,d=n.data.length;c<d;c++){var h=n.data[c];h=(typeof h=="string")?[h]:h;var r=n.formatMatch(h,c+1,n.data.length);if(r===false){continue}var s=r.charAt(0).toLowerCase();if(!e[s]){e[s]=[]}var g={value:r,data:h,result:n.formatResult&&n.formatResult(h)||r};e[s].push(g);if(f++<n.max){e[""].push(g)}}b.each(e,function(p,o){n.cacheLength++;j(p,o)})}setTimeout(l,25);function a(){k={};m=0}return{flush:a,add:j,populate:l,load:function(g){if(!n.cacheLength||!m){return null}if(!n.url&&n.matchContains){var c=[];for(var e in k){if(e.length>0){var f=k[e];b.each(f,function(o,h){if(i(h.value,g)){c.push(h)}})}}return c}else{if(k[g]){return k[g]}else{if(n.matchSubset){for(var d=g.length-1;d>=n.minChars;d--){var f=k[g.substr(0,d)];if(f){var c=[];b.each(f,function(o,h){if(i(h.value,g)){c[c.length]=h}});return c}}}}}return null}}};b.Autocompleter.Select=function(G,B,z,v){var C={ACTIVE:"ac_over"};var A,F=-1,t,y="",a=true,I,w;function x(){if(!a){return}I=b("<div/>").hide().addClass(G.resultsClass).css("position","absolute").appendTo(document.body);w=b("<ul/>").appendTo(I).mouseover(function(c){if(u(c).nodeName&&u(c).nodeName.toUpperCase()=="LI"){F=b("li",w).removeClass(C.ACTIVE).index(u(c));b(u(c)).addClass(C.ACTIVE)}}).click(function(c){b(u(c)).addClass(C.ACTIVE);z();B.focus();return false}).mousedown(function(){v.mouseDownOnSelect=true}).mouseup(function(){v.mouseDownOnSelect=false});if(G.width>0){I.css("width",G.width)}a=false}function u(c){var d=c.target;while(d&&d.tagName!="LI"){d=d.parentNode}if(!d){return[]}return d}function D(e){A.slice(F,F+1).removeClass(C.ACTIVE);E(e);var c=A.slice(F,F+1).addClass(C.ACTIVE);if(G.scroll){var d=0;A.slice(0,F).each(function(){d+=this.offsetHeight});if((d+c[0].offsetHeight-w.scrollTop())>w[0].clientHeight){w.scrollTop(d+c[0].offsetHeight-w.innerHeight())}else{if(d<w.scrollTop()){w.scrollTop(d)}}}}function E(c){F+=c;if(F<0){F=A.size()-1}else{if(F>=A.size()){F=0}}}function J(c){return G.max&&G.max<c?G.max:c}function H(){w.empty();var e=J(t.length);for(var d=0;d<e;d++){if(!t[d]){continue}var c=G.formatItem(t[d].data,d+1,e,t[d].value,y);if(c===false){continue}var f=b("<li/>").html(G.highlight(c,y)).addClass(d%2==0?"ac_even":"ac_odd").appendTo(w)[0];b.data(f,"ac_data",t[d])}A=w.find("li");if(G.selectFirst){A.slice(0,1).addClass(C.ACTIVE);F=0}if(b.fn.bgiframe){w.bgiframe()}}return{display:function(c,d){x();t=c;y=d;H()},next:function(){D(1)},prev:function(){D(-1)},pageUp:function(){if(F!=0&&F-8<0){D(-F)}else{D(-8)}},pageDown:function(){if(F!=A.size()-1&&F+8>A.size()){D(A.size()-1-F)}else{D(8)}},hide:function(){I&&I.hide();A&&A.removeClass(C.ACTIVE);F=-1},visible:function(){return I&&I.is(":visible")},current:function(){return this.visible()&&(A.filter("."+C.ACTIVE)[0]||G.selectFirst&&A[0])},show:function(){var c=b(B).offset();I.css({width:typeof G.width=="string"||G.width>0?G.width:b(B).width(),top:c.top+B.offsetHeight,left:c.left}).show();if(G.scroll){w.scrollTop(0);w.css({maxHeight:G.scrollHeight,overflow:"auto"});if(b.browser.msie&&typeof document.body.style.maxHeight==="undefined"){var e=0;A.each(function(){e+=this.offsetHeight});var d=e>G.scrollHeight;w.css("height",d?G.scrollHeight:e);if(!d){A.width(w.width()-parseInt(A.css("padding-left"))-parseInt(A.css("padding-right")))}}}},selected:function(){var c=A&&A.filter("."+C.ACTIVE).removeClass(C.ACTIVE);return c&&c.length&&b.data(c[0],"ac_data")},emptyList:function(){w&&w.empty()},unbind:function(){I&&I.remove()}}};b.Autocompleter.Selection=function(g,f,h){if(g.setSelectionRange){g.setSelectionRange(f,h)}else{if(g.createTextRange){var a=g.createTextRange();a.collapse(true);a.moveStart("character",f);a.moveEnd("character",h);a.select()}else{if(g.selectionStart){g.selectionStart=f;g.selectionEnd=h}}}g.focus()}})(jQuery);