package com.yappy.search_engine.controller;

import com.yappy.search_engine.dto.SearchByParameterDto;
import com.yappy.search_engine.dto.SearchRequestDto;
import com.yappy.search_engine.dto.VideoSearchResult;
import com.yappy.search_engine.service.MediaContentService;
import com.yappy.search_engine.service.SearchService;
import com.yappy.search_engine.service.SuggestionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

@RestController
public class SearchController {

    private final SearchService searchService;
    private final SuggestionService suggestionService;
    private final MediaContentService mediaContentService;

    @Autowired
    public SearchController(SearchService searchService, SuggestionService suggestionService,
                            MediaContentService mediaContentService) {
        this.searchService = searchService;
        this.suggestionService = suggestionService;
        this.mediaContentService = mediaContentService;
    }

    @PostMapping("/search")
    public VideoSearchResult searchWithFilter(@RequestParam(defaultValue = "1971-01-01")
                                                @DateTimeFormat(pattern = "yyyy-MM-dd")
                                                Date date,
                                              @RequestBody SearchRequestDto dto) {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS");
        String formattedDate = formatter.format(date);

        return searchService.searchWithFilter(dto, formattedDate);
    }

    /**
     * This is the end point for inspectors
     * @param query
     * @param page
     * @param size
     * @return all results
     */
    @GetMapping("/search/text")
    public VideoSearchResult searchVideoText(@RequestParam String query,
                                                      @RequestParam(defaultValue = "0") int page,
                                                      @RequestParam(defaultValue = "15") int size) {
        return searchService.searchVideoText(query.trim(), page, size);
    }

    @PostMapping("/search/full-text")
    public VideoSearchResult searchVideoFullText(@RequestParam(defaultValue = "0") int page,
                                                      @RequestParam(defaultValue = "15") int size,
                                                 @RequestBody SearchByParameterDto searchByParameterDto) {
        return searchService.searchVideoFullText(searchByParameterDto, page, size);
    }

    @PostMapping("/search/embedding")
    public VideoSearchResult searchByEmbedding(@RequestParam(defaultValue = "0") int page,
                                               @RequestParam(defaultValue = "15") int size,
                                               @RequestBody SearchByParameterDto searchByParameterDto) {
        return searchService.searchVideosByEmbedding(searchByParameterDto, page, size);
    }

    @PostMapping("/search/combine")
    public VideoSearchResult searchByCombine(@RequestParam(defaultValue = "0") int page,
                                               @RequestParam(defaultValue = "15") int size,
                                               @RequestBody SearchByParameterDto searchByParameterDto) {
        return searchService.searchVideosByCombine(searchByParameterDto, page, size);
    }






    @GetMapping("/search/autocomplete")
    public List<String> autocomplete(@RequestParam(defaultValue = "0") int page,
                                     @RequestParam(defaultValue = "10") int size,
                                     @RequestParam String query) {
        return suggestionService.getAutocomplete(query, page, size);
    }
    @GetMapping("/indexing-time")
    public String indexingTime(@RequestParam String uuid) {
        return mediaContentService.getIndexingTime(uuid);
    }
}