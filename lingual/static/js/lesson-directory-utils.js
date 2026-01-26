function goToLesson(slug) {
    const url = lessonUrl.replace("__SLUG__", slug);
    window.location.href = url;
}