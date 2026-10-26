from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from agents.resume_parser import extract_text, parse_resume, ResumeError
from .models import Resume
from agents.orchestrator import run_agent


def sid(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


class Base(APIView):
    authentication_classes = []   # no auth required; session cookie identifies the user
    permission_classes = []


class UploadView(Base):
    parser_classes = [MultiPartParser]

    def post(self, request):
        f = request.FILES.get("file")
        if not f:
            return Response({"error": "No file uploaded."}, status=400)
        try:
            data = parse_resume(extract_text(f))
        except ResumeError as e:
            return Response({"error": str(e)}, status=400)
        Resume.objects.update_or_create(session_key=sid(request), defaults={"data": data})
        return Response({"resume": data})


class ChatView(Base):
    def post(self, request):
        msg = (request.data.get("message") or "").strip()
        if not msg:
            return Response({"error": "Message is empty."}, status=400)
        if len(msg) > 2000:
            return Response({"error": "Message too long (max 2000 characters)."}, status=400)
        # Pass the full request so orchestrator can read/write the session job map
        return Response({"reply": run_agent(sid(request), msg, request=request)})