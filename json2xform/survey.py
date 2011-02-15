from .question import MultipleChoiceQuestion
from .section import Section

class Survey(Section):
    
    def _build_options_list_from_descendants(self):
        """
        used in preparation for exporting to XForm
        """
        self._options_list = []
        for element in self._elements:
            element.add_options_to_list(self._options_list)

        return self._options_list
    
