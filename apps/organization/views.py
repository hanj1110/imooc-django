import json

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
# Create your views here.

from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from .models import CourseOrg, CityDict
from .forms import UserAskForm
from operation.models import UserFavorite
from users.models import UserProfile


# 课程机构列表页，筛选页
class OrgView(View):
    def get(self, request):
        all_orgs = CourseOrg.objects.all()
        hot_orgs = all_orgs.order_by('-click_nums')[:3]
        all_citys = CityDict.objects.all()

        # 取出筛选城市
        city_id = request.GET.get('city', '')
        if city_id:
            all_orgs = all_orgs.filter(city_id=int(city_id))

        # 课程机构类别筛选
        category = request.GET.get('ct', '')
        if category:
            all_orgs = all_orgs.filter(category=category)

        # 排序
        sort = request.GET.get('sort', '')
        if sort == 'students':
            all_orgs = all_orgs.order_by('-students')
        elif sort == 'courses':
            all_orgs = all_orgs.order_by('-course_nums')

        #筛选完成之后再进行统计
        org_nums = all_orgs.count()

        # 分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_orgs, 2, request=request)

        orgs = p.page(page)

        return render(request, 'org-list.html', {
            'all_orgs': orgs,
            'all_citys': all_citys,
            'org_nums': org_nums,
            'city_id': city_id,
            'sort': sort,
            'category': category,
            'hot_orgs': hot_orgs,
        })


# 用户添加咨询课程表单提交
class AddUserAskView(View):
    def post(self, request):
        user_ask_form = UserAskForm(request.POST)
        res = dict()
        if user_ask_form.is_valid():
            user_ask_form.save(commit=True)
            res['status'] = 'success'
        else:
            res['status'] = 'fail'
            res['msg'] = '添加出错'
        return HttpResponse(json.dumps(res), content_type='application/json')


# 课程机构详情页的首页
class OrgHomeView(View):
    def get(self, request, org_id):
        course_org = CourseOrg.objects.get(id=int(org_id))

        # 取出某个指定课程机构下所有的课程(course)
        # 语法 course + _set
        all_courses = course_org.course_set.all()[:3]

        # 取出某个指定课程机构下所有的老师(course)
        all_teachers = course_org.teacher_set.all()[:1]

        # 初始化判断是否收藏
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        current_page = 'home'

        return render(request, 'org-detail-homepage.html', {
            'all_courses': all_courses,
            'all_teachers': all_teachers,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


# 课程机构详情页讲师页面
class OrgCourseView(View):
    def get(self, request, org_id):
        current_page = 'course'
        course_org = CourseOrg.objects.get(id=int(org_id))
        all_courses = course_org.course_set.all()

        #初始化判断是否收藏
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id = course_org.id, fav_type=2):
                has_fav = True

        return render(request, 'org-detail-course.html', {
            'all_courses': all_courses,
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


class OrgDescView(View):
    # 课程机构介绍页
    def get(self, request, org_id):
        current_page = 'desc'
        course_org = CourseOrg.objects.get(id=int(org_id))

        # 初始化判断是否收藏
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        return render(request, 'org-detail-desc.html', {
            'course_org': course_org,
            'current_page': current_page,
            'has_fav': has_fav,
        })


# 课程机构详情页讲师页面
class OrgTeacherView(View):
    def get(self, request, org_id):
        current_page = 'teacher'
        course_org = CourseOrg.objects.get(id=int(org_id))
        all_teachers = course_org.teacher_set.all()

        # 初始化判断是否收藏
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        return render(request, 'org-detail-teachers.html', {
            'all_teachers': all_teachers,
            'current_page': current_page,
            'course_org': course_org,
            'has_fav': has_fav,
        })


class AddFavView(View):
    # 用户收藏、取消收藏 课程机构
    def post(self, request):
        fav_id = request.POST.get('fav_id', 0)
        fav_type = request.POST.get('fav_type', 0)

        #判断用户登录状态
        if not request.user.is_authenticated():
            res = {}
            res['status'] = 'fail'
            res['msg'] = u'用户未登录'
            return HttpResponse(json.dumps(res), content_type='application/json')

        # 查询收藏记录
        exist_records = UserFavorite.objects.filter(user=request.user, fav_id=int(fav_id), fav_type=int(fav_type))

        # 收藏已经存在
        res = {}
        if exist_records:
            # 如果记录已经存在，则表示用户取消收藏
            exist_records.delete()
            res['status'] = 'success'
            res['msg'] = u'收藏'
        else:
            user_fav = UserFavorite()
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.user = request.user
                user_fav.fav_id = int(fav_id)
                user_fav.fav_type = int(fav_type)
                # 完成收藏需要三个字段 user_id，fav_id， fav_type
                user_fav.save()

                res['status'] = 'success'
                res['msg'] = u'已收藏'
            else:
                res['status'] = 'fail'
                res['msg'] = u'收藏出错'

        return HttpResponse(json.dumps(res), content_type='application/json')
