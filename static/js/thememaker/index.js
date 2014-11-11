"use strict";

$(function() {
  scroll_to_tab_listener();
  infinitescroll_listener();
  slider_listener();
  expand_theme_listener();
  install_cover_theme_listener();
  install_theme_listener();
});

function scroll_to_tab_listener() {
  var path = window.location.pathname;
  var isScroll = false;
  isScroll = (path.indexOf("new") > -1)? true : isScroll;
  isScroll = (path.indexOf("fav") > -1)? true : isScroll;
  isScroll = (path.indexOf("hot") > -1)? true : isScroll;

  if (isScroll) {
    $('html, body').animate({
      scrollTop: $("#theme_list").offset().top
    }, 2000);
  }

}

function infinitescroll_listener() {
  $('#theme_wrap').infinitescroll({
    navSelector: '#page-nav',
    nextSelector: '#page-nav > a',
    itemSelector: 'li.theme_row',
        //debug: true,
        loadingImg: '',
        loadingText: '',
        donetext: '',
        animate: true
      }, function() {
        expand_theme_listener();
        install_theme_listener();
      });
}

function install_cover_theme_listener() {
  $('#cover_theme a.install').on('click', function(e){
    var $that = $(this);
    var li_tag = $that.parent().parent();
    var theme = {
      id         : li_tag.attr('theme-id'),
      name       : li_tag.children('h3.meta_title').attr('title'),
      headerURL  : li_tag.children('div.demo_section').children('span.demo_bg').attr('header-img'),
      footerURL  : '/static/uploads/theme_maker/user/00.png',
      textcolor  : li_tag.children('div.demo_section').children('span.demo_font1').attr('color'),
      accentcolor: li_tag.children('div.demo_section').children('span.demo_mask').attr('color'),
    };
    setTheme($that.get(0), theme, INSTALL);
  });
}

function install_theme_listener() {
  $('div.theme_bottom_btn > a.install').unbind();
  $('div.theme_bottom_btn > a.install').on('click', function(e){
    var $that = $(this);
    e.preventDefault();
    e.stopPropagation();
    var li_tag = $that.parent().parent();
    var theme = {
      id         : li_tag.attr('theme-id'),
      name       : li_tag.children('h3.meta_title').attr('title'),
      headerURL  : li_tag.children('dl').children('dt').children('img').attr('header-img'),
      footerURL  : '/static/uploads/theme_maker/user/00.png',
      textcolor  : li_tag.children('dl').children('dd.theme_text').attr('color'),
      accentcolor: li_tag.children('dl').children('dd.theme_mask').attr('color'),
    };
    setTheme($that.get(0), theme, INSTALL);
  });
}

function expand_theme_listener() {
  $('div.theme_container > ul > li').unbind();
  $('div.theme_container > ul > li').on('click', function(e){
    e.preventDefault();
    e.stopPropagation();
    var $that = $(this);
    var expand = $that.children('div.theme_bottom_btn').children('a.expand');
    var isOpen = expand.hasClass('on');
    var li_tag = $that;
    var ul_tag = $that.parent();
    var li_idx = $(ul_tag).children('li').index(li_tag) + 1;
    var div_tag = $that.parent().parent();
    

    $('div.theme_bottom_btn > a.expand').removeClass('on');
    $('#theme_detail').slideUp(400, function(){
      $('#expand_arrow').removeClass('arrow01 arrow02 arrow03').addClass('arrow0' + li_idx);  
      $(div_tag).after($('#theme_detail'));
      fill_data(li_tag);
    });
    if (!isOpen) {
      expand.addClass('on');
      $('#theme_detail').slideDown(400);
    }   
  });

  $('a.btn_close').unbind();
  $('a.btn_close').on('click', function(e){
    e.preventDefault();
    $('#theme_detail').slideUp(400);
    $('div.theme_bottom_btn > a.expand').removeClass('on');
  });

  // fill data into #theme_detail element
  function fill_data(ele) {
    var p_tag = ele.children('p.tab_type');
    var meta_title = ele.children('h3').text();
    var meta_desc = ele.children('p.meta_desc').text();
    var meta_date = p_tag.children('span.type_latest').text();
    var meta_download = p_tag.children('span.type_hot').text();
    var meta_likes = p_tag.children('span.type_favorite').text();
    var preview_img = ele.children('dl').children('dt').children('img').attr('src');
    var color = ele.children('dl').children('dd.theme_mask').attr('color');

    $('#theme_detail_panel h3').text(meta_title);
    $('#theme_detail_panel p').text(meta_desc);
    $('#theme_detail_panel ul li.info_date').text(meta_date);
    $('#theme_detail_panel ul li.info_download').text(meta_download);
    $('#theme_detail_panel ul li.info_fb').text(meta_likes);
    $('#theme_detail_panel div.demo_section span.demo_bg').css("background-image", "url('" + preview_img + "')");
    $('div#theme_detail').removeClass('Whitecolor Redcolor Yellowcolor Greencolor Bluecolor');
    $('div#theme_detail').addClass(color);
  }
}

function slider_listener() {
  $($("#cover_list > ul > li").get(0)).children('a').addClass('on');

  var slider = $("#cover_ul");

  slider.owlCarousel({
    slideSpeed : 300,
    paginationSpeed : 400,
    singleItem: true,
    pagination: false,
    autoPlay: 3000,
    stopOnHover: true,
    afterMove: function(){
      var that = this;
      update_slider_status(that.currentItem);
    },
  });

  $(".cover_next").on('click', function(e) {
    e.preventDefault();
    slider.trigger('owl.next');
  });

  $(".cover_pre").on('click', function(e) {
    e.preventDefault();
    slider.trigger('owl.prev');
  });

  // slider_pagination
  $("#cover_list > ul > li").on('click', function(e){
    var $that = $(this);
    e.preventDefault();
    var slider = $("#cover_ul").data('owlCarousel');
    var index = $that.index();
    slider.goTo(index);
  });

  function update_slider_status(pos) {
    var item = $("#cover_list > ul > li").get(pos);
    var color = $(item).children('div.demo_section').children('span.demo_mask').attr('color');
    $('div#main_cover').removeClass('Whitecolor Redcolor Yellowcolor Greencolor Bluecolor');
    $('div#main_cover').addClass(color);
    $("#cover_list > ul > li > a").removeClass('on');
    $(item).children('a').addClass('on');
  }
}

