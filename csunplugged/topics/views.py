"""Views for the topics application."""

from django.shortcuts import get_object_or_404
from django.views import generic
from django.http import JsonResponse, Http404
from general.templatetags.render_html_field import render_html_with_static

from .models import (
    Topic,
    CurriculumIntegration,
    UnitPlan,
    Lesson,
    ProgrammingExercise,
    ProgrammingExerciseLanguageImplementation,
    ConnectedGeneratedResource,
    GlossaryTerm,
)


class IndexView(generic.ListView):
    """View for the topics application homepage."""

    template_name = 'topics/index.html'
    context_object_name = 'all_topics'

    def get_queryset(self):
        """Get queryset of all topics.

        Returns:
            Queryset of Topic objects ordered by name.
        """
        return Topic.objects.order_by('name')


class TopicView(generic.DetailView):
    """View for a specific topic."""

    model = Topic
    template_name = 'topics/topic.html'
    slug_url_kwarg = 'topic_slug'

    def get_context_data(self, **kwargs):
        """Provide the context data for the topic view.

        Returns:
            Dictionary of context data.
        """
        # Call the base implementation first to get a context
        context = super(TopicView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the connected unit plans
        unit_plans = UnitPlan.objects.filter(topic=self.object).order_by('name').select_related()
        for unit_plan in unit_plans:
            unit_plan.lessons = unit_plan.lessons_by_age_group()
        context['unit_plans'] = unit_plans
        # Add in a QuerySet of all the connected curriculum integrations
        context['curriculum_integrations'] = CurriculumIntegration.objects.filter(topic=self.object).order_by('number')
        return context


class UnitPlanView(generic.DetailView):
    """View for a specific unit plan."""

    model = UnitPlan
    template_name = 'topics/unit_plan.html'
    context_object_name = 'unit_plan'

    def get_object(self, **kwargs):
        """Retrieve object for the unit plan view.

        Returns:
            UnitPlan object, or raises 404 error if not found.
        """
        return get_object_or_404(
            self.model.objects.select_related(),
            topic__slug=self.kwargs.get('topic_slug', None),
            slug=self.kwargs.get('unit_plan_slug', None)
        )

    def get_context_data(self, **kwargs):
        """Provide the context data for the unit plan view.

        Returns:
            Dictionary of context data.
        """
        # Call the base implementation first to get a context
        context = super(UnitPlanView, self).get_context_data(**kwargs)
        # Loading object under consistent context names for breadcrumbs
        context['topic'] = self.object.topic
        # Add all the connected lessons
        context['lessons'] = self.object.unit_plan_lessons.order_by('min_age', 'max_age', 'number')
        return context


class LessonView(generic.DetailView):
    """View for a specific lesson."""

    model = Lesson
    template_name = 'topics/lesson.html'
    context_object_name = 'lesson'

    def get_object(self, **kwargs):
        """Retrieve object for the lesson view.

        Returns:
            Lesson object, or raises 404 error if not found.
        """
        return get_object_or_404(
            self.model.objects.select_related(),
            topic__slug=self.kwargs.get('topic_slug', None),
            unit_plan__slug=self.kwargs.get('unit_plan_slug', None),
            slug=self.kwargs.get('lesson_slug', None),
        )

    def get_context_data(self, **kwargs):
        """Provide the context data for the lesson view.

        Returns:
            Dictionary of context data.
        """
        # Call the base implementation first to get a context
        context = super(LessonView, self).get_context_data(**kwargs)
        # Loading objects under consistent context names for breadcrumbs
        context['topic'] = self.object.topic
        context['unit_plan'] = self.object.unit_plan
        # Add all the connected programming exercises
        context['programming_exercises'] = self.object.programming_exercises.all()
        # Add all the connected curriculum areas
        context['lesson_curriculum_areas'] = self.object.curriculum_areas.all()
        # Add all the connected learning outcomes
        context['lesson_learning_outcomes'] = self.object.learning_outcomes.all()
        # Add all the connected generated resources
        related_resources = self.object.generated_resources.all()
        generated_resources = []
        for related_resource in related_resources:
            generated_resource = dict()
            generated_resource['slug'] = related_resource.slug
            generated_resource['name'] = related_resource.name
            generated_resource['thumbnail'] = related_resource.thumbnail_static_path
            relationship = ConnectedGeneratedResource.objects.get(resource=related_resource, lesson=self.object)
            generated_resource['description'] = relationship.description
            generated_resources.append(generated_resource)
        context['lesson_generated_resources'] = generated_resources

        return context


class ProgrammingExerciseList(generic.ListView):
    """View for listing all programming exercises for a lesson."""

    model = ProgrammingExercise
    template_name = 'topics/programming_exercise_lesson_list.html'
    context_object_name = 'all_programming_exercises'

    def get_queryset(self, **kwargs):
        """Retrieve all programming exercises for a topic.

        Returns:
            Queryset of ProgrammingExercise objects.
        """
        lesson_slug = self.kwargs.get('lesson_slug', None)
        exercises = ProgrammingExercise.objects.filter(lessons__slug=lesson_slug)
        return exercises.order_by('exercise_set_number', 'exercise_number')

    def get_context_data(self, **kwargs):
        """Provide the context data for the programming exercise list view.

        Returns:
            Dictionary of context data.
        """
        context = super(ProgrammingExerciseList, self).get_context_data(**kwargs)
        lesson = get_object_or_404(
            Lesson.objects.select_related(),
            topic__slug=self.kwargs.get('topic_slug', None),
            unit_plan__slug=self.kwargs.get('unit_plan_slug', None),
            slug=self.kwargs.get('lesson_slug', None),
        )
        context['lesson'] = lesson
        context['unit_plan'] = lesson.unit_plan
        context['topic'] = lesson.topic
        return context


class ProgrammingExerciseView(generic.DetailView):
    """View for a specific programming exercise."""

    model = ProgrammingExercise
    template_name = 'topics/programming_exercise.html'
    context_object_name = 'programming_exercise'

    def get_object(self, **kwargs):
        """Retrieve object for the programming exercise view.

        Returns:
            ProgrammingExercise object, or raises 404 error if not found.
        """
        return get_object_or_404(
            self.model.objects.select_related(),
            topic__slug=self.kwargs.get('topic_slug', None),
            slug=self.kwargs.get('programming_exercise_slug', None)
        )

    def get_context_data(self, **kwargs):
        """Provide the context data for the programming exercise view.

        Returns:
            Dictionary of context data.
        """
        # Call the base implementation first to get a context
        context = super(ProgrammingExerciseView, self).get_context_data(**kwargs)
        context['lessons'] = self.object.lessons.all()
        context['topic'] = self.object.topic
        # Add all the connected learning outcomes
        context['programming_exercise_learning_outcomes'] = self.object.learning_outcomes.all()
        context['implementations'] = self.object.implementations.all().order_by('-language__name').select_related()
        return context


class ProgrammingExerciseLanguageSolutionView(generic.DetailView):
    """View for a language implementation for a programming exercise."""

    model = ProgrammingExerciseLanguageImplementation
    template_name = 'topics/programming_exercise_language_solution.html'
    context_object_name = 'implementation'

    def get_object(self, **kwargs):
        """Retrieve object for the language implementation view.

        Returns:
            ProgrammingExerciseLanguageImplementation object, or raises 404
            error if not found.
        """
        return get_object_or_404(
            self.model.objects.select_related(),
            topic__slug=self.kwargs.get('topic_slug', None),
            exercise__slug=self.kwargs.get('programming_exercise_slug', None),
            language__slug=self.kwargs.get('programming_language_slug', None)
        )

    def get_context_data(self, **kwargs):
        """Provide the context data for the language implementation view.

        Returns:
            Dictionary of context data.
        """
        # Call the base implementation first to get a context
        context = super(ProgrammingExerciseLanguageSolutionView, self).get_context_data(**kwargs)
        # Loading object under consistent context names for breadcrumbs
        context['topic'] = self.object.topic
        context['programming_exercise'] = self.object.exercise
        return context


class CurriculumIntegrationList(generic.ListView):
    """View for list all curriculum inegrations for a topic."""

    model = CurriculumIntegration
    template_name = 'topics/curriculum_integration_list.html'
    context_object_name = 'all_curriculum_integrations'

    def get_queryset(self, **kwargs):
        """Retrieve all curriculum integrations for a topic.

        Returns:
            Queryset of CurriculumIntegration objects.
        """
        return CurriculumIntegration.objects.filter(
            topic__slug=self.kwargs.get('topic_slug', None)
        ).select_related().order_by('number')

    def get_context_data(self, **kwargs):
        """Provide the context data for the curriculum integration list view.

        Returns:
            Dictionary of context data.
        """
        context = super(CurriculumIntegrationList, self).get_context_data(**kwargs)
        # Loading objects under consistent context names for breadcrumbs
        context['topic'] = get_object_or_404(Topic, slug=self.kwargs.get('topic_slug', None))
        return context


class AllCurriculumIntegrationList(generic.ListView):
    """View for listing all curriculum integrations."""

    model = CurriculumIntegration
    template_name = 'topics/all_curriculum_integration_list.html'
    context_object_name = 'curriculum_integrations'

    def get_queryset(self, **kwargs):
        """Retrieve all curriculum integrations.

        Returns:
            Queryset of CurriculumIntegration objects.
        """
        return CurriculumIntegration.objects.select_related().order_by('topic__name', 'number')


class CurriculumIntegrationView(generic.DetailView):
    """View for a specific curriculum integration."""

    model = CurriculumIntegration
    queryset = CurriculumIntegration.objects.all()
    template_name = 'topics/curriculum_integration.html'
    context_object_name = 'integration'

    def get_object(self, **kwargs):
        """Retrieve object for the curriculum integration view.

        Returns:
            CurriculumIntegration object, or raises 404 error if not found.
        """
        return get_object_or_404(
            self.model.objects.select_related(),
            topic__slug=self.kwargs.get('topic_slug', None),
            slug=self.kwargs.get('integration_slug', None)
        )

    def get_context_data(self, **kwargs):
        """Provide the context data for the curriculum integration view.

        Returns:
            Dictionary of context data.
        """
        # Call the base implementation first to get a context
        context = super(CurriculumIntegrationView, self).get_context_data(**kwargs)
        # Loading objects under consistent context names for breadcrumbs
        context['topic'] = self.object.topic
        # Add in a QuerySet of all the connected curriculum areas
        context['integration_curriculum_areas'] = self.object.curriculum_areas.all()
        # Add in a QuerySet of all the prerequisite lessons
        context['prerequisite_lessons'] = self.object.prerequisite_lessons.select_related().order_by(
            'unit_plan__name', 'number'
        )
        return context


class OtherResourcesView(generic.DetailView):
    """View for detailing other resources for a specific topic."""

    model = Topic
    template_name = 'topics/topic-other-resources.html'
    slug_url_kwarg = 'topic_slug'


class GlossaryList(generic.ListView):
    """Provide glossary view of all terms."""

    template_name = "topics/glossary.html"
    context_object_name = "glossary_terms"

    def get_queryset(self):
        """Get queryset of all glossary terms.

        Returns:
            Queryset of GlossaryTerm objects ordered by term.
        """
        return GlossaryTerm.objects.order_by("term")


def glossary_json(request, **kwargs):
    """Provide JSON data for glossary term.

    Args:
        request: The HTTP request.

    Returns:
        JSON response is sent containing data for the requested term.
    """
    # If term parameter, then return JSON
    if "term" in request.GET:
        glossary_slug = request.GET.get("term")
        glossary_item = get_object_or_404(
            GlossaryTerm,
            slug=glossary_slug
        )
        data = {
            "slug": glossary_slug,
            "term": glossary_item.term,
            "definition": render_html_with_static(glossary_item.definition)
        }
        return JsonResponse(data)
    else:
        raise Http404("Term parameter not specified.")